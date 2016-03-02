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

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class product_product(models.Model):
    _inherit = "product.product"

    @api.one
    def _get_no_wh_internal_stock(self):
        warehouse_obj = self.env["stock.warehouse"]
        loc_obj = self.env["stock.location"]
        warehouses = warehouse_obj.search([])
        view_loc_ids = [x.view_location_id.id for x in warehouses]
        locs = loc_obj.search([('usage', '=', 'internal'), '!',
                               ('id', 'child_of', view_loc_ids)])
        qty = self.with_context(location=[x.id for x in locs]).qty_available
        self.qty_available_wo_wh = qty

    qty_available_wo_wh = fields.\
        Float(string="Qty. on kitchen", compute="_get_no_wh_internal_stock",
              readonly=True,
              digits=dp.get_precision('Product Unit of Measure'))

