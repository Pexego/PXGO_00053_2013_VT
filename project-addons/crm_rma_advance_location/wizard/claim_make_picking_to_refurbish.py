from odoo import fields, models, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time


class ClaimMakePickingToRefurbishWizard(models.TransientModel):
    _name = "claim.make.picking.to.refurbish.wizard"

    @staticmethod
    def get_lots_remaining_moves(move):
        """ This function returns the lot_text not used in other moves
        :param move: original stock.move from incoming picking
        :return: set() set of lots text
        """
        lot_text = set(move.lots_text.split(','))
        children_lots_text = set(move.child_move_ids.mapped('lots_text'))
        return lot_text - children_lots_text

    @api.model
    def _get_picking_lines(self):
        wiz_lines = []
        for move in self.env['stock.picking'].browse(self.env.context['active_id']).move_lines:
            if move.qty_used >= move.product_uom_qty:
                continue
            new_line = {'product_id': move.product_id.id,
                        'move_id': move.id,
                        'product_qty': 1}
            product = move.product_id
            domain = [('claim_type', '=',
                       self.env.ref('crm_claim_type.crm_claim_type_supplier').id),
                      ('stage_id', '=', self.env.ref('crm_claim.stage_claim5').id)]
            if product.product_brand_id.code in ['Ajax', 'HIKVISION']:
                domain += [('partner_id', 'in', product.seller_ids.ids)]
            else:
                domain += [('partner_id', '=', product.last_supplier_id.id)]
            claim_id = self.env['crm.claim'].search(domain)
            if claim_id and len(claim_id) == 1:
                new_line.update({'claim_id': claim_id.id})
            qty = move.product_uom_qty - move.qty_used
            not_used_lots_text = self.get_lots_remaining_moves(move)
            for __ in range(int(qty)):
                new_line_dict = {}
                if not_used_lots_text:
                    new_line_dict = {'prodlot_id':not_used_lots_text.pop()}
                new_line_dict.update(new_line)
                wiz_lines.append(new_line_dict)
        if not wiz_lines:
            raise exceptions.UserError(_("All units are already processed"))
        return wiz_lines

    @api.model
    def _get_source_loc(self):
        warehouse_id = self._get_default_warehouse()
        return warehouse_id.lot_rma_id.id

    @api.model
    def _get_dest_loc(self):
        return self.env.ref('location_moves.stock_location_damaged').id

    picking_line_source_location = fields.Many2one('stock.location',
                                                   'Source Location',
                                                   help="Location where the returned products are from.",
                                                   required=True, default=_get_source_loc)
    picking_line_dest_location = fields.Many2one('stock.location',
                                                 'Dest. Location',
                                                 help="Location where the system will stock the returned products.",
                                                 required=True, default=_get_dest_loc)
    picking_line_ids = fields.One2many('claim.make.picking.to.refurbish.line',
                                       'wizard_id',
                                       'Picking lines', default=_get_picking_lines)

    @api.model
    def _get_default_warehouse(self):
        warehouse_id = self.env['crm.claim']._get_default_warehouse()
        return warehouse_id

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_create_picking(self):
        if self.picking_line_ids.filtered(lambda line: line.problem_description is False):
            raise exceptions.UserError(
                _("All products must have a description of the problem, please fill it out and try again"))
        picking_obj = self.env['stock.picking']
        type_ids = self.env['stock.picking.type'].search([('code', '=', 'outgoing')])
        note = 'Internal picking from RMA to refurbish'
        prev_picking = picking_obj.browse(self.env.context['active_id'])
        partner_id = prev_picking.partner_id.id
        default_picking_data = {
            'move_lines': [],
            'location_id': self.picking_line_source_location.id,
            'location_dest_id': self.picking_line_dest_location.id,
            'picking_type_id': type_ids and type_ids[0].id,
            'note': note,
            'claim_id': prev_picking.claim_id.id,
            'partner_id': partner_id
        }
        picking_id = prev_picking.copy(default_picking_data)
        moves_qty = {}
        for wizard_picking_line in self.picking_line_ids:
            wizard_move = wizard_picking_line.move_id
            if wizard_picking_line.product_qty > (wizard_move.product_uom_qty - wizard_move.qty_used):
                raise exceptions.UserError(_("You cannot send more than %i of this product %s")
                                           % (int(wizard_move.product_uom_qty - wizard_move.qty_used),
                                              wizard_move.product_id.default_code))
            default_move_data = {
                'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'date_expected': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'partner_id': partner_id,
                'picking_id': picking_id.id,
                'company_id': prev_picking.company_id.id,
                'location_id': self.picking_line_source_location.id,
                'location_dest_id': self.picking_line_dest_location.id,
                'note': note,
                'picking_type_id': type_ids and type_ids[0].id,
                'product_uom_qty': 1,
                'origin_move_id': wizard_move.id,
                'lots_text':wizard_picking_line.prodlot_id
            }
            new_move = wizard_picking_line.move_id.copy(default_move_data)
            if wizard_move in moves_qty:
                new_moves, qty = moves_qty[wizard_move]
                new_moves += new_move
                moves_qty[wizard_move] = (new_moves, qty+1)
            else:
                moves_qty[wizard_move] = (new_move, 1)

        if picking_id:
            picking_id.with_context({'claim_mode': True}).action_assign()
            picking_id.action_done()
        for n_moves, qty in moves_qty.values():
            deposit = n_moves[0].origin_move_id.claim_line_id.deposit_id
            if deposit:
                if qty < deposit.product_uom_qty:
                    new_deposit = deposit.copy()
                    new_deposit.write({'product_uom_qty': qty})
                    deposit.write({'product_uom_qty': deposit.product_uom_qty - qty})
                    new_deposit.set_damaged(picking_id)
                else:
                    deposit.set_damaged(picking_id)

        rmps = self.env['crm.claim']
        for l in self.picking_line_ids:
            product = l.move_id.product_id
            suppliers = self.env['res.partner']
            if l.claim_id:
                rmp_id = self.env['crm.claim'].browse(l.claim_id.id)
            else:
                domain = [('claim_type', '=',
                           self.env.ref('crm_claim_type.crm_claim_type_supplier').id),
                          ('stage_id', '=', self.env.ref('crm_claim.stage_claim5').id)]
                if product.product_brand_id.code in eval(
                        self.env['ir.config_parameter'].sudo().get_param('brands_seller_ids_rmp')):
                    if product.normal_product_id:
                        suppliers += product.normal_product_id.seller_ids.mapped('name')
                    else:
                        suppliers += product.seller_ids.mapped('name')
                    domain_p = domain + [('partner_id', 'in', suppliers.ids)]
                else:
                    if product.normal_product_id:
                        suppliers += product.normal_product_id.last_supplier_id
                    else:
                        suppliers += product.last_supplier_id
                    domain_p = domain + [('partner_id', '=', suppliers.id)]
                rmp_id = self.env['crm.claim'].search(domain_p)
                suppliers_p = suppliers.mapped('rmp_partner')
                if not rmp_id and suppliers:
                    suppliers += suppliers_p
                    rmp_id = self.env['crm.claim'].search(domain + [('partner_id', 'in', suppliers_p.ids)])
                if not rmp_id:
                    raise exceptions.UserError(
                        _("There is no RMP in progress for this supplier (%s)") %
                        suppliers.mapped('name'))
                elif len(rmp_id) > 1:
                    raise exceptions.UserError(
                        _("There are %i RMP in progress for this supplier (%s). (%s)") % (
                            len(rmp_id), suppliers.mapped('name'), rmp_id.mapped('number')))

            line_domain = {
                'product_id': product.id,
                'name': l.problem_description,
                'claim_origine': 'broken_down',
                'product_returned_quantity': 1,
                'claim_id': rmp_id.id,
                'prodlot_id': l.prodlot_id,
                'printed': False,
                'supplier_id': rmp_id.partner_id.id,
                'substate_id': self.env.ref('crm_claim_rma_custom.substate_checked').id
            }
            if product.normal_product_id:
                line_domain['product_id'] = product.normal_product_id.id
            if not l.prodlot_id:
                sec_list = self.env['crm.claim'].browse(rmp_id.id).claim_line_ids.mapped('sequence')
                if sec_list:
                    seq = max(sec_list) + 1
                else:
                    seq = 0
                line_domain['prodlot_id'] = seq
            self.env['claim.line'].create(line_domain)
            rmps += rmp_id

        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        result['context'] = {}
        res = self.env.ref('stock.view_picking_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = picking_id.id
        message = _("Products successfully entered in the following RMPs %s") % rmps.mapped('number')
        picking_id.env.user.notify_info(message=message)
        return result

    select_claim = fields.Boolean()


class ClaimMakePickingToRefurbishLine(models.TransientModel):
    _name = "claim.make.picking.to.refurbish.line"

    move_id = fields.Many2one('stock.move')
    prodlot_id = fields.Char("Product Lot / Serial")
    problem_description = fields.Char()
    wizard_id = fields.Many2one('claim.make.picking.to.refurbish.wizard')
    product_id = fields.Many2one('product.product')
    product_qty = fields.Float()
    claim_id = fields.Many2one("crm.claim", domain=lambda self: [('claim_type', '=',
                                                                  self.env.ref(
                                                                      'crm_claim_type.crm_claim_type_supplier').id),
                                                                 ('stage_id', '=',
                                                                  self.env.ref('crm_claim.stage_claim5').id)])
