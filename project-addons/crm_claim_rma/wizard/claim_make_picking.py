##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, _, exceptions, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time


class ClaimMakePickingLine(models.TransientModel):
    _name = "claim.make.picking.wizard.line"

    product_id = fields.Many2one('product.product')
    product_qty = fields.Float()
    deposit_id = fields.Many2one('stock.deposit')
    prodlot_id = fields.Char(
            string='Serial/Lot n°',
            help="The serial/lot of the returned product")
    substate_id = fields.Many2one(
        'substate.substate',
        string='Sub state',
        help="Select a sub state to precise the standard state. Example 1:"
             " state = refused; substate could be warranty over, not in "
             "warranty, no problem,... . Example 2: state = to treate; "
             "substate could be to refund, to exchange, to repair,...")
    claim_line_id = fields.Many2one('claim.line')
    equivalent_product_id = fields.Many2one('product.product')


class ClaimMakePicking(models.TransientModel):
    _name = "claim_make_picking.wizard"
    _description = 'Wizard to create pickings from claim lines'

    # Get default destination location
    @api.model
    def _get_dest_loc(self):
        """Return the location_id to use as destination.
        If it's an outoing shippment: take the customer stock property
        If it's an incoming shippment take the location_dest_id common to all
        lines, or if different, return None."""
        context = self.env.context
        loc_id = False
        supplier_type = self.env.ref('crm_claim_type.crm_claim_type_supplier').id
        customer_type = self.env.ref('crm_claim_type.crm_claim_type_customer').id
        if context.get('picking_type') == 'out':
            partner = self.env['res.partner'].browse(context.get('partner_id'))
            if context.get('type') == supplier_type:
                loc_id = partner.property_stock_supplier
            elif context.get('type') == customer_type:
                loc_id = partner.property_stock_customer
        elif context.get('picking_type') == 'in':
            loc_id = self.env.get('crm_rma_advance_location.stock_location_rma')
        return loc_id

    @api.model
    def _get_claim_lines(self):
        context = self.env.context
        line_obj = self.env['claim.line']
        good_lines = []
        domain = [('claim_id', '=', context['active_id'])]
        if context.get('picking_type') == 'out':
            domain += [('deposit_id','=',False)]
        line_ids = line_obj.search(domain)
        for line in line_ids:
            if context.get('picking_type') == 'out':
                moves = line.move_ids.filtered(lambda m: m.picking_code == self.env.ref(
                    'stock.picking_type_out').code and m.location_dest_id.usage in ['supplier',
                                                                                    'customer'] and m.state != 'cancel')
            else:
                moves = line.move_ids.filtered(lambda m: m.picking_code == self.env.ref(
                    'stock.picking_type_in').code and m.location_dest_id == self.env.ref(
                    'crm_rma_advance_location.stock_location_rma') and m.state != 'cancel')
            product_moves_qty = sum(moves.mapped('product_uom_qty'))
            if product_moves_qty < line.product_returned_quantity:
                good_lines.append({'product_id': line.product_id.id,
                                   'equivalent_product_id': line.equivalent_product_id.id,
                                   'product_qty': line.product_returned_quantity - product_moves_qty,
                                   'claim_line_id': line.id,
                                   'deposit_id': line.deposit_id.id,
                                   'substate_id': line.substate_id.id,
                                   'prodlot_id': line.prodlot_id
                                   })
        if not good_lines:
            raise exceptions.UserError(_('All units are already processed'))
        return good_lines

    # Get default source location
    def _get_source_loc(self):
        loc_id = False
        context = self.env.context
        supplier_type = self.env.ref('crm_claim_type.crm_claim_type_supplier').id
        customer_type = self.env.ref('crm_claim_type.crm_claim_type_customer').id
        if context.get('picking_type') == 'out':
            warehouse = self.env['stock.warehouse'].browse(context.get('warehouse_id'))
            if context.get('type') == supplier_type:
                loc_id = warehouse.lot_breakdown_id
            if context.get('type') == customer_type:
                loc_id = warehouse.lot_rma_id

        elif context.get('picking_type') == 'in':
            partner = self.env['res.partner'].browse(context.get('partner_id'))
            if context.get('type') == supplier_type:
                loc_id = partner.property_stock_supplier

            if context.get('type') == customer_type:
                loc_id = partner.property_stock_customer
        return loc_id

    claim_line_source_location = fields.Many2one(
        'stock.location',
        string='Source Location',
        help="Location where the returned products are from.",
        required=True, default=_get_source_loc)
    claim_line_dest_location = fields.Many2one(
        'stock.location',
        string='Dest. Location',
        help="Location where the system will stock the returned products.",
        required=True, default=_get_dest_loc)
    claim_line_ids = fields.Many2many(
        'claim.make.picking.wizard.line',
        string='Claim lines', default=_get_claim_lines)

    @api.multi
    def create_move(self, wizard_line, p_type, picking_id, claim, note):
        type_ids = self.env['stock.picking.type'].search([('code', '=', p_type)])
        partner_id = claim.delivery_address_id
        move_obj = self.env['stock.move']
        claim_line = wizard_line.claim_line_id
        product = claim_line.product_id
        context = self.env.context
        qty = wizard_line.product_qty
        if context.get('picking_type', 'in') == u'out' and claim_line.equivalent_product_id:
                product = claim_line.equivalent_product_id
        move_id = move_obj.create(
            {'name': product.name,
             'priority': '0',
             'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
             'date_expected': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
             'product_id': product.id,
             'picking_type_id': type_ids and type_ids[0].id,
             'product_uom_qty': qty,
             'product_uom': product.uom_id.id,
             'partner_id': partner_id.id,
             'picking_id': picking_id.id,
             'state': 'draft',
             'price_unit': claim_line.unit_sale_price,
             'company_id': claim.company_id.id,
             'location_id': picking_id.location_id.id,
             'location_dest_id': picking_id.location_dest_id.id,
             'note': note,
             'claim_line_id': claim_line.id
             })

    # If "Create" button pressed
    def action_create_picking(self):
        lines_with_deposits = self.env['claim.make.picking.wizard.line']
        pickings = self.env['stock.picking']
        for line in self.claim_line_ids:
            claim_line = line.claim_line_id
            if self.env.context.get('picking_type') == 'out':
                moves = claim_line.move_ids.filtered(lambda m: m.picking_code == self.env.ref(
                    'stock.picking_type_out').code and m.location_dest_id.usage in ['supplier',
                                                                                    'customer'] and m.state != 'cancel')
            else:
                moves = claim_line.move_ids.filtered(lambda m: m.picking_code == self.env.ref(
                    'stock.picking_type_in').code and m.location_dest_id == self.env.ref(
                    'crm_rma_advance_location.stock_location_rma') and m.state != 'cancel')
            product_moves_qty = sum(moves.mapped('product_uom_qty'))
            if claim_line.product_returned_quantity - product_moves_qty - line.product_qty < 0:
                raise exceptions.UserError(_("It is not possible to create pickings with more units than there are in "
                                             "the RMA"))
        p_type=self.env.context.get('picking_type')
        if p_type in ['in','out']:
            lines_with_deposits = self.claim_line_ids.filtered(lambda c: c.claim_line_id.deposit_id)
            if lines_with_deposits:
                pick = self.create_picking(lines_with_deposits, deposit_mode=True)
                pickings |= pick
                for line in lines_with_deposits:
                    deposit = line.claim_line_id.deposit_id
                    if line.product_qty < deposit.product_uom_qty:
                        new_deposit = deposit.copy()
                        new_deposit.write({'product_uom_qty': deposit.product_uom_qty - line.product_qty})
                        deposit.write({'product_uom_qty': line.product_qty})
                    if p_type == 'in':
                        move = pick.move_lines.filtered(lambda m: m.claim_line_id == line.claim_line_id)
                        deposit.set_rma(move)
                    else:
                        deposit.set_draft()

        lines = self.claim_line_ids - lines_with_deposits
        if lines:
            pickings |= self.create_picking(lines)
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    def create_picking(self, claim_lines, deposit_mode=False):
        picking_obj = self.env['stock.picking']
        claim_obj = self.env['crm.claim']
        note = 'RMA picking out'
        context = self.env.context

        location_id = self.claim_line_source_location
        location_dest_id = self.claim_line_dest_location

        claim = claim_obj.browse(context['active_id'])
        partner_id = claim.delivery_address_id
        not_sync = False
        picking_type = context.get('picking_type',"")
        if picking_type == 'out':
            p_type = 'outgoing'
        else:
            p_type = 'incoming'
            not_sync = True
            note = 'RMA picking ' + str(p_type)
        if claim_lines and deposit_mode:
            deposit = claim_lines[0].claim_line_id.deposit_id
            if picking_type == 'in':
                location_id = deposit.move_id.location_dest_id
            elif picking_type == 'out':
                location_dest_id = deposit.move_id.location_dest_id

        # create picking
        type_ids = self.env['stock.picking.type'].search([('code', '=', p_type)])
        picking_id = picking_obj.create(
            {'origin': claim.number,
             'picking_type_id': type_ids and type_ids[0].id,
             'move_type': 'one',  # direct
             'state': 'draft',
             'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
             'partner_id': partner_id.id,
             'invoice_state': "none",
             'company_id': claim.company_id.id,
             'location_id': location_id.id,
             'location_dest_id': location_dest_id.id,
             'note': note,
             'claim_id': claim.id,
             'not_sync':not_sync
             })
        # Create picking lines
        for wizard_claim_line in claim_lines:
            self.create_move(wizard_claim_line, p_type, picking_id, claim, note)

        if picking_id:
            picking_id.action_assign()

        return picking_id
