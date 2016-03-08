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


class ClaimMakePicking(models.TransientModel):

    _inherit = "claim_make_picking.wizard"

    odoo_management = fields.Boolean('Management in Odoo')

    @api.onchange('claim_line_source_location', 'claim_line_dest_location')
    def onchange_locations(self):
        if self.claim_line_source_location.odoo_management:
            if self.claim_line_dest_location == \
                    self.env.ref('stock.stock_location_customers'):
                self.odoo_management = True
            else:
                self.odoo_management = False
        else:
            self.odoo_management = False

    @api.multi
    def action_create_picking(self):
        res = super(ClaimMakePicking, self).action_create_picking()
        if self.odoo_management:
            if not self.claim_line_source_location.odoo_management:
                raise exceptions.Warning(_("The origin location is not managed"
                                           " by Odoo."))
            if res.get('res_id', False):
                pick = self.env["stock.picking"].browse(res['res_id'])
                pick.odoo_management = True

        return res
