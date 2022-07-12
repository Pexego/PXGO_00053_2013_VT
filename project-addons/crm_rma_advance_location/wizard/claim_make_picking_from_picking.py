#########################################################################
#                                                                       #
#                                                                       #
#########################################################################
#                                                                       #
# crm_claim_rma for OpenERP                                             #
# Copyright (C) 2009-2012  Akretion, Emmanuel Samyn,                    #
#       Benoît GUILLOT <benoit.guillot@akretion.com>                    #
# This program is free software: you can redistribute it and/or modify   #
# it under the terms of the GNU General Public License as published by   #
# the Free Software Foundation, either version 3 of the License, or      #
# (at your option) any later version.                                    #
#                                                                       #
# This program is distributed in the hope that it will be useful,        #
# but WITHOUT ANY WARRANTY; without even the implied warranty of         #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
# GNU General Public License for more details.                           #
#                                                                       #
# You should have received a copy of the GNU General Public License      #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
from odoo import fields, models, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time


class ClaimMakePickingFromPickingLine(models.TransientModel):
    _name = "claim_make_picking_from_picking_line"
    product_id = fields.Many2one('product.product', related='move_id.product_id')
    product_qty = fields.Float()
    partner_id = fields.Many2one(related='move_id.partner_id')
    move_id = fields.Many2one('stock.move')


class ClaimMakePickingFromPicking(models.TransientModel):
    _name = "claim_make_picking_from_picking.wizard"
    _description = "Wizard to create pickings from picking lines"

    @api.model
    def _get_picking_lines(self):
        lines = self.env['claim_make_picking_from_picking_line']
        for move in self.env['stock.picking'].browse(self.env.context['active_id']).move_lines:
            if move.qty_used < move.product_uom_qty:
                lines |= self.env['claim_make_picking_from_picking_line'].create({
                    'move_id': move.id,
                    'product_qty': move.product_uom_qty - move.qty_used
                })
        if not lines:
            raise exceptions.UserError(_("All units are already processed"))
        return lines

    # Get default source location
    @api.model
    def _get_source_loc(self):
        warehouse_id = self._get_default_warehouse()
        return warehouse_id.lot_rma_id.id

    # Get default destination location
    @api.model
    def _get_dest_loc(self):
        warehouse_id = self._get_default_warehouse()
        if self.env.context.get('picking_type'):
            context_loc = self.env.context.get('picking_type')[8:]
            if context_loc != "input":
                loc_field = 'lot_%s_id' % context_loc
            else:
                loc_field = "wh_input_stock_loc_id"
            loc_id = warehouse_id.read([loc_field])[0][loc_field][0]
        return loc_id

    picking_line_source_location = fields.Many2one('stock.location',
                                                   'Source Location',
                                                   help="Location where the returned products are from.",
                                                   required=True, default=_get_source_loc)
    picking_line_dest_location = fields.Many2one('stock.location',
                                                 'Dest. Location',
                                                 help="Location where the system will stock the returned products.",
                                                 required=True, default=_get_dest_loc)
    picking_line_ids = fields.Many2many('claim_make_picking_from_picking_line',
                                        'claim_picking_line_claim_picking',
                                        'claim_picking_id',
                                        'picking_line_id',
                                        'Picking lines', default=_get_picking_lines)

    @api.model
    def _get_default_warehouse(self):
        warehouse_id = self.env['crm.claim']._get_default_warehouse()
        return warehouse_id

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    # If "Create" button pressed
    @api.multi
    def action_create_picking_from_picking(self):
        products = self.picking_line_ids.mapped('product_id').filtered(lambda x: x.state == 'make_to_order')
        picking_obj = self.env['stock.picking']
        view_obj = self.env['ir.ui.view']
        context = self.env.context
        if context.get('p_type', False):
            p_type = context['p_type']
        else:
            p_type = 'internal'
        type_ids = self.env['stock.picking.type'].search([('code', '=', p_type)])
        if context.get('picking_type'):
            context_type = context.get('picking_type')[8:]
            note = 'Internal picking from RMA to %s' % context_type
            name = 'Internal picking to %s' % context_type
        view_id = view_obj.search([('xml_id', '=', 'view_picking_form'),
                                   ('model', '=', 'stock.picking'),
                                   ('type', '=', 'form'),
                                   ('name', '=', 'stock.picking.form')])[0]
        wizard = self
        prev_picking = picking_obj.browse(context['active_id'])
        partner_id = prev_picking.partner_id.id
        default_picking_data = {
            'move_lines': [],
            'location_id': wizard.picking_line_source_location.id,
            'location_dest_id': wizard.picking_line_dest_location.id,
            'picking_type_id': type_ids and type_ids[0].id,
            'note': note,
            'claim_id': prev_picking.claim_id.id,
            'partner_id': prev_picking.claim_id.company_id.partner_id.id
        }
        picking_id = prev_picking.copy(default_picking_data)
        moves_qty = {}
        for wizard_picking_line in wizard.picking_line_ids:
            wizard_move = wizard_picking_line.move_id
            if wizard_picking_line.product_qty > (wizard_move.product_uom_qty - wizard_move.qty_used):
                raise exceptions.UserError(_("You cannot send more than %i of this product %s")
                                           % (int(wizard_move.product_uom_qty - wizard_move.qty_used),
                                              wizard_move.product_id.default_code))
            default_move_data = {
                'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'date_expected': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'partner_id': prev_picking.partner_id.id,
                'picking_id': picking_id.id,
                'company_id': prev_picking.company_id.id,
                'location_id': wizard.picking_line_source_location.id,
                'location_dest_id': wizard.picking_line_dest_location.id,
                'note': note,
                'picking_type_id': type_ids and type_ids[0].id,
                'product_uom_qty': wizard_picking_line.product_qty,
                'origin_move_id': wizard_move.id
            }
            move_id = wizard_picking_line.move_id.copy(default_move_data)
            wizard_move.qty_used += wizard_picking_line.product_qty
            if wizard_move in moves_qty:
                moves_qty[move_id] += wizard_picking_line.product_qty
            else:
                moves_qty[move_id] = wizard_picking_line.product_qty

        if picking_id:
            picking_id.action_assign()
            # if we validate the picking, it fails because there is no quantity available
            # picking_id.button_validate()
        picking_type = context.get('picking_type', '')
        if picking_type in ['picking_input', 'picking_breakage_loss']:
            for n_move, qty in moves_qty.items():
                deposit = n_move.origin_move_id.claim_line_id.deposit_id
                if deposit:
                    if qty < deposit.product_uom_qty:
                        old_deposit = deposit
                        deposit = old_deposit.copy()
                        deposit.write({'product_uom_qty': qty})
                        old_deposit.write({'product_uom_qty': old_deposit.product_uom_qty - qty})
                    if picking_type == 'picking_input':
                        deposit.return_deposit(claim_id=picking_id.claim_id)
                    else:
                        deposit.deposit_loss()
        if products:
            message = _("You shouldn't send the following products to stock due to they are 'make to order' %s. "
                        "Please check the picking (%s) carefully before validate it") % (
                      str(products.mapped('default_code')), picking_id.name)
            self.env.user.notify_warning(message=message, sticky=True)

        domain = "[('picking_type_code','=','%s'),('partner_id','=',%s)]" % (p_type, partner_id)
        return {
            'name': '%s' % name,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'domain': domain,
            'res_model': 'stock.picking',
            'res_id': picking_id.id,
            'type': 'ir.actions.act_window',
        }
