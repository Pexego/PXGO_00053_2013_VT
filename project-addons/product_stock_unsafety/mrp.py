# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos S.L.
#    $Omar Castiñeira Saavedra$ <omar@comunitea.com>
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

from openerp import models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def action_production_end(self):
        res = super(MrpProduction, self).action_production_end()
        under_min = self.env['product.stock.unsafety']
        for production in self:
            domain = [
                ('state', '=', 'in_action'),
                ('production_id', '=', production.id)
            ]
            under_min_objs = under_min.search(domain)
            if under_min_objs:
                under_min_objs.write({'state': 'finalized'})

        return res

    @api.multi
    def unlink(self):
        under_min_obj = self.env['product.stock.unsafety']
        for production in self:
            under_mins = under_min_obj.search([('production_id', '=',
                                                production.id)])
            if under_mins:
                under_mins.write({"state": "in_progress",
                                  "production_id": False})
        return super(MrpProduction, self).unlink()
