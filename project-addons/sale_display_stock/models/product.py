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

import math
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from collections import defaultdict

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def _get_no_wh_internal_stock(self):
        for product in self.sudo():
            locs = []
            locs.append(self.env.ref('location_moves.stock_location_kitchen').id)
            locs.append(self.env.ref('location_moves.stock_location_pantry').id)
            qty = product.with_context(location=locs).qty_available
            product.qty_available_wo_wh = qty


    @api.multi
    def _get_input_loc_stock(self):
        for product in self:
            locs = []
            qty = 0.0
            for wh in self.env["stock.warehouse"].search([]):
                locs.append(wh.wh_input_stock_loc_id.id)
                qty += product.with_context(location=locs).qty_available
            product.qty_available_input_loc = qty

    @api.multi
    def _get_in_production_stock(self):
        for product in self:
            if product.product_variant_ids:
                moves = self.env["stock.move"].search([('product_id', 'in', product.product_variant_ids.ids),
                                                       ('purchase_line_id', '!=', False),
                                                       ('picking_id', '=', False),
                                                       ('state', '!=', 'cancel')])
                product.qty_in_production = sum(moves.mapped('product_uom_qty')) or 0.0
            else:
                product.qty_in_production = 0.0

    @api.multi
    def _stock_conservative(self):
        for product in self:
            pack_stock = 0
            first_subproduct = True
            if product.bom_ids:
                for bom in product.bom_ids:
                    if bom.type == 'phantom':
                        for subproduct in bom.bom_line_ids:
                            subproduct_quantity_next = subproduct.product_qty
                            if subproduct_quantity_next:
                                subproduct_stock_next = \
                                    subproduct.product_id.qty_available - subproduct.product_id.outgoing_picking_reserved_qty - \
                                    subproduct.product_id.reservation_count
                                pack_stock_next = math.\
                                    floor(subproduct_stock_next /
                                          subproduct_quantity_next)
                                if first_subproduct:
                                    pack_stock = pack_stock_next
                                    first_subproduct = False
                                else:
                                    if pack_stock_next < pack_stock:
                                        pack_stock = pack_stock_next
                        product.virtual_stock_conservative = pack_stock
                    else:
                        product.virtual_stock_conservative = \
                            product.qty_available - product.outgoing_picking_reserved_qty - product.reservation_count
            else:
                product.virtual_stock_conservative = \
                    product.qty_available - product.outgoing_picking_reserved_qty - product.reservation_count

    @api.multi
    def _get_avail_conservative(self):
        for product in self:
            pack_stock = 0
            first_subproduct = True
            if product.bom_ids:
                for bom in product.bom_ids:
                    if bom.type == 'phantom':
                        for subproduct in bom.bom_line_ids:
                            subproduct_quantity_next = subproduct.product_qty
                            if subproduct_quantity_next:
                                subproduct_stock_next = \
                                    subproduct.product_id.qty_available - subproduct.product_id.outgoing_picking_reserved_qty - \
                                    subproduct.product_id.reservation_count - \
                                    subproduct.product_id.qty_available_wo_wh - \
                                    subproduct.product_id.qty_available_input_loc
                                pack_stock_next = math.\
                                    floor(subproduct_stock_next /
                                          subproduct_quantity_next)
                                if first_subproduct:
                                    pack_stock = pack_stock_next
                                    first_subproduct = False
                                else:
                                    if pack_stock_next < pack_stock:
                                        pack_stock = pack_stock_next
                        product.virtual_available_wo_incoming = pack_stock
                    else:
                        product.virtual_available_wo_incoming = \
                            product.virtual_stock_conservative - \
                            product.qty_available_wo_wh - \
                            product.qty_available_input_loc
            else:
                product.virtual_available_wo_incoming = \
                    product.virtual_stock_conservative - \
                    product.qty_available_wo_wh - \
                    product.qty_available_input_loc

    qty_available_wo_wh = fields.\
        Float(string="Qty. on kitchen", compute="_get_no_wh_internal_stock",
              readonly=True,
              digits=dp.get_precision('Product Unit of Measure'))

    outgoing_picking_reserved_qty = fields.Float(
        compute='_get_outgoing_picking_qty', readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))
    qty_available_input_loc = fields.\
        Float(string="Qty. on input", compute="_get_input_loc_stock",
              readonly=True,
              digits=dp.get_precision('Product Unit of Measure'))
    qty_in_production = fields.\
        Float("Qty. in production", compute="_get_in_production_stock",
              readonly=True,
              digits=dp.get_precision('Product Unit of Measure'))
    virtual_available_wo_incoming = fields.\
        Float("Virtual avail. conservative",
              compute="_get_avail_conservative",
              readonly=True,
              digits=dp.get_precision('Product Unit of Measure'))

    @api.multi
    def _get_outgoing_picking_qty(self):
        for product in self:
            domain = [('product_id', 'in', product.product_variant_ids.ids),
                      ('state', 'in', ('confirmed', 'assigned', 'partially_available', 'waiting')),
                      ('picking_id', '!=', False),
                      ('location_id', '=', self.env.ref('stock.stock_location_stock').id)]
            product.outgoing_picking_reserved_qty = sum(item['product_uom_qty'] for item in self.env['stock.move'].search_read(domain, ['product_uom_qty']))

    @api.multi
    def _get_stock_italy(self):
        location_id = self.env['stock.location'].search([('name', '=', 'Depósito Visiotech Italia')]).id
        for product in self:
            qty = product.with_context(location=location_id).qty_available
            product.qty_available_italy = qty

    qty_available_italy = fields.Float(string="Qty. available Italy", compute="_get_stock_italy",
                             readonly=True,
                             digits=dp.get_precision('Product Unit of Measure'))


class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    def _stock_conservative(self):
        for product in self:
            pack_stock = 0
            first_subproduct = True
            if product.bom_ids:
                for bom in product.bom_ids:
                    if bom.type == 'phantom':
                        for subproduct in bom.bom_line_ids:
                            subproduct_quantity_next = subproduct.product_qty
                            if subproduct_quantity_next:
                                product_id = subproduct.product_id
                                subproduct_stock_next = \
                                    product_id.qty_available - \
                                    product_id.outgoing_picking_reserved_qty - \
                                    product_id.reservation_count
                                pack_stock_next = math.\
                                    floor(subproduct_stock_next /
                                          subproduct_quantity_next)
                                if first_subproduct:
                                    pack_stock = pack_stock_next
                                    first_subproduct = False
                                else:
                                    if pack_stock_next < pack_stock:
                                        pack_stock = pack_stock_next
                        product.virtual_stock_conservative = pack_stock
                    else:
                        product.virtual_stock_conservative = \
                            product.qty_available - product.outgoing_picking_reserved_qty - product.reservation_count
            else:
                product.virtual_stock_conservative = \
                    product.qty_available - product.outgoing_picking_reserved_qty - product.reservation_count

    @api.multi
    def _compute_reservation_count(self):
        """
            Overrides the original function in order to calculate the reservation_count as the sum of the
            stock.reservation quantity of sale.orders + stock.move quantity of the mrp.productions
            that are not in progress
        """
        # Get the stock.reservation's quantity of sale.orders
        reservations = self.env['stock.reservation'].read_group(
            [('product_id', 'in', self.ids),
             ('state', 'in', ['draft', 'confirmed', 'assigned', 'partially_available']),
             ('mrp_id', '=', False)],
            ['product_id', 'product_qty'],
            groupby='product_id')
        # Get the stock.move's quantity of the mrp.productions that are not in progress
        moves =  self.env['stock.move'].read_group([('product_id', 'in', self.ids),
                      ('state', 'in', ('confirmed', 'assigned', 'partially_available', 'waiting')),
                      ('raw_material_production_id', '!=', False),
                      ('picking_id', '=', False)],
            ['product_id', 'product_uom_qty'],
            groupby='product_id')
        dicc = defaultdict(int)
        for res in reservations:
            product = res.get('product_id')[0]
            dicc[product] += res.get('product_qty')
        for move in moves:
            product = move.get('product_id')[0]
            dicc[product] += move.get('product_uom_qty')
        for product in self:
            product.reservation_count= dicc.get(product.id) or 0
