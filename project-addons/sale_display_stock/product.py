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
        locs = []
        locs.append(self.env.ref('location_moves.stock_location_kitchen').id)
        locs.append(self.env.ref('location_moves.stock_location_pantry').id)
        qty = self.with_context(location=locs).qty_available
        self.qty_available_wo_wh = qty

    qty_available_wo_wh = fields.\
        Float(string="Qty. on kitchen", compute="_get_no_wh_internal_stock",
              readonly=True,
              digits=dp.get_precision('Product Unit of Measure'))

    outgoing_picking_reserved_qty = fields.Float(
        compute='_get_outgoing_picking_qty', readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))

    @api.one
    def _get_outgoing_picking_qty(self):
        moves = self.env['stock.move'].search(
            [('product_id', '=', self.id),
             ('state', 'in', ('confirmed', 'assigned')),
             ('picking_id.picking_type_code', '=', 'outgoing')])
        self.outgoing_picking_reserved_qty = sum(moves.mapped(
            'reserved_availability'))
