# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from openerp import models, api, fields, exceptions, _


class ClaimMakePickingFromPicking(models.TransientModel):

    _inherit = "claim_make_picking_from_picking.wizard"

    odoo_management = fields.Boolean('Management in Odoo')
    not_sync = fields.Boolean("Not sync", help="This picking not will be "
                                               "synced with Vstock",
                              readonly=True)

    @api.onchange('picking_line_source_location', 'picking_line_dest_location')
    def onchange_locations(self):
        if self.picking_line_source_location.odoo_management:
            if self.picking_line_dest_location == \
                    self.env.ref('stock.stock_location_customers'):
                self.odoo_management = True
            else:
                self.odoo_management = False
        else:
            self.odoo_management = False
        if self.picking_line_dest_location.not_sync:
            self.not_sync = True
        else:
            self.not_sync = False

    @api.multi
    def action_create_picking_from_picking(self):
        res = super(ClaimMakePickingFromPicking, self).\
            action_create_picking_from_picking()
        if self.odoo_management or (self.not_sync or
                                    self.picking_line_dest_location.not_sync):
            if self.odoo_management and \
                    not self.picking_line_dest_location.odoo_management:
                raise exceptions.Warning(_("The origin location is not managed"
                                           " by Odoo."))
            if res.get('res_id', False):
                pick = self.env["stock.picking"].browse(res['res_id'])
                pick.odoo_management = self.odoo_management
                pick.not_sync = self.not_sync or \
                    self.picking_line_dest_location.not_sync

        return res
