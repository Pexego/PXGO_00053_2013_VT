# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos
#    $Carlos Lombardía Rodríguez <carlos@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from openerp import models, fields, api


class stock_picking(models.Model):
    _inherit = "stock.picking"

    internal_notes = fields.Text("Internal Notes", copy=False)
    odoo_management = fields.Boolean("Odoo management", readonly=True,
                                     copy=False)
    not_sync = fields.Boolean("Not sync", help="This picking not will be "
                                               "synced with Vstock",
                              copy=True)

    @api.multi
    def copy(self, default=None):
        default = default and default or {}
        if self.env.context.get('picking_type', '') == 'picking_input':
            default['not_sync'] = False
        return super(stock_picking, self).copy(default)


    def action_assign(self, cr, uid, ids, context=None):
        res = super(stock_picking, self).action_assign(cr, uid, ids,
                                                       context=context)
        for obj in self.browse(cr, uid, ids):
            if obj.claim_id and obj.picking_type_code == "incoming":
                obj.force_assign()

        return res

    @api.model
    def do_transfer(self):
        for picking in self:
            if picking.claim_id:
                for move in picking.move_lines:
                    if move.claim_line_id:
                        if picking.picking_type_code == 'incoming':
                            move.claim_line_id.substate_id = self.env.ref(
                                'crm_claim_rma_custom.substate_received')
                        elif picking.picking_type_code == 'outgoing':
                            if move.claim_line_id.equivalent_product_id:
                                move.claim_line_id.substate_id = self.env.ref(
                                    'crm_claim_rma_custom.substate_replaced')
                            elif not move.claim_line_id.repair_id:
                                move.claim_line_id.substate_id = self.env.ref(
                                    'crm_claim_rma_custom.substate_checked')
        return super(stock_picking, self).do_transfer()


class StockLocation(models.Model):

    _inherit = "stock.location"

    odoo_management = fields.Boolean('Management in Odoo',
                                     help="The outputs of this location are "
                                          "managed in Odoo, Vstock only will "
                                          "print shipping labels")
    not_sync = fields.Boolean("Not sync",
                              help="The incomimg pickings to this location "
                                   "not will be synced with vstock")


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_done(self):
        res = super(stock_move, self).action_done()
        for move in self:
            if move.claim_line_id:
                claim_line_obj = move.claim_line_id
                if claim_line_obj.claim_type == u'supplier':
                    qty = claim_line_obj.product_returned_quantity
                    loc_lost = self.env.ref('crm_rma_advance_location.stock_location_carrier_loss')
                    claim_obj = claim_line_obj.claim_id
                    if claim_line_obj.equivalent_product_id:
                        rma_cost = claim_obj.rma_cost
                        if move.location_dest_id == loc_lost:
                            standard_price = claim_line_obj.product_id.standard_price
                            rma_cost += (move.picking_type_code == u'incoming') and (standard_price * qty) or 0.0
                        else:
                            standard_price = claim_line_obj.equivalent_product_id.standard_price
                            rma_cost += (move.picking_type_code == u'outgoing') and (standard_price * qty) or 0.0
                        claim_obj.rma_cost = rma_cost
                    elif move.location_dest_id == loc_lost:
                        standard_price = claim_line_obj.product_id.standard_price
                        rma_cost = claim_obj.rma_cost
                        rma_cost += (move.picking_type_code == u'incoming') and (standard_price * qty) or 0.0
                        claim_obj.rma_cost = rma_cost

        return res

