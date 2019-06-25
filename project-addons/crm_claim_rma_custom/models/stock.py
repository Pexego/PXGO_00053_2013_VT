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
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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
        return super(StockPicking, self).copy(default)

    @api.multi
    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        for obj in self:
            if obj.claim_id and obj.picking_type_code == "incoming":
                obj.force_assign()

        return res

    @api.model
    def action_done(self):
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
        return super(StockPicking, self).action_done()


class StockLocation(models.Model):

    _inherit = "stock.location"

    odoo_management = fields.Boolean('Management in Odoo',
                                     help="The outputs of this location are "
                                          "managed in Odoo, Vstock only will "
                                          "print shipping labels")
    not_sync = fields.Boolean("Not sync",
                              help="The incomimg pickings to this location "
                                   "not will be synced with vstock")


