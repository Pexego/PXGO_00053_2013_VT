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

import math
from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.one
    def _get_no_wh_internal_stock(self):
        locs = []
        locs.append(self.env.ref('location_moves.stock_location_kitchen').id)
        locs.append(self.env.ref('location_moves.stock_location_pantry').id)
        qty = self.with_context(location=locs).qty_available
        self.qty_available_wo_wh = qty

    @api.one
    def _get_external_stock(self):
        locs = [self.env.ref('location_moves.stock_location_external').id]
        qty = self.with_context(location=locs).qty_available
        self.qty_available_external = qty

    @api.one
    def _get_input_loc_stock(self):
        locs = []
        qty = 0.0
        for wh in self.env["stock.warehouse"].search([]):
            locs.append(wh.wh_input_stock_loc_id.id)
            qty += self.with_context(location=locs).qty_available
        self.qty_available_input_loc = qty

    @api.one
    def _get_in_production_stock(self):
        if self.product_variant_ids:
            moves = self.env["stock.move"].search([('product_id', 'in',
                                                    self.product_variant_ids.ids),
                                                    ('purchase_line_id', '!=',
                                                    False),
                                                    ('picking_id', '=', False),
                                                    ('state', '!=', 'cancel')])

            qty = 0.0
            for move in moves:
                qty += move.product_uom_qty
            self.qty_in_production = qty
        else:
            self.qty_in_production = 0.0

    @api.one
    def _stock_conservative(self):
        pack_stock = 0
        first_subproduct = True
        product_product_obj = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
        if product_product_obj.pack_line_ids:
            for subproduct in product_product_obj.pack_line_ids:
                subproduct_quantity_next = subproduct.quantity
                if subproduct_quantity_next:
                    result = subproduct.product_id._product_available()[subproduct.product_id.id]
                    subproduct_stock_next = result['qty_available'] - result['outgoing_qty']
                    pack_stock_next = math.floor(subproduct_stock_next / subproduct_quantity_next)
                    if first_subproduct:
                        pack_stock = pack_stock_next
                        first_subproduct = False
                    else:
                        if pack_stock_next < pack_stock:
                            pack_stock = pack_stock_next
            self.virtual_stock_conservative = pack_stock
        else:
            self.virtual_stock_conservative = self.qty_available - self.outgoing_qty - \
                                              self.qty_available_wo_wh - self.qty_available_input_loc

    @api.one
    def _get_avail_conservative(self):
        pack_stock = 0
        first_subproduct = True
        product_product_obj = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
        if product_product_obj.pack_line_ids:
            for subproduct in product_product_obj.pack_line_ids:
                subproduct_quantity_next = subproduct.quantity
                if subproduct_quantity_next:
                    result = subproduct.product_id._product_available()[subproduct.product_id.id]
                    subproduct_stock_next = result['qty_available'] - result['outgoing_qty']
                    pack_stock_next = math.floor(subproduct_stock_next / subproduct_quantity_next)
                    if first_subproduct:
                        pack_stock = pack_stock_next
                        first_subproduct = False
                    else:
                        if pack_stock_next < pack_stock:
                            pack_stock = pack_stock_next
            self.virtual_available_wo_incoming = pack_stock
        else:
            self.virtual_available_wo_incoming = self.qty_available - self.outgoing_qty

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
    qty_available_external = fields.\
        Float(string="Qty. in external loc.", compute="_get_external_stock",
              readonly=True,
              digits=dp.get_precision('Product Unit of Measure'))
    qty_in_production = fields.\
        Float("Qty. in production",compute="_get_in_production_stock",
              readonly=True,
              digits=dp.get_precision('Product Unit of Measure'))
    virtual_available_wo_incoming = fields.\
        Float("Virtual avail. conservative",compute="_get_avail_conservative",
              readonly=True,
              digits=dp.get_precision('Product Unit of Measure'))

    @api.one
    def _get_outgoing_picking_qty(self):
        self._cr.execute("""select sum(product_uom_qty) from stock_move sm
 inner join procurement_order po on po.id = sm.procurement_id
 inner join stock_picking_type spt on spt.id = sm.picking_type_id
 where sm.state in ('confirmed', 'assigned') and spt.code = 'outgoing'
 and po.sale_line_id is not null and sm.product_id in (%s)""" %
                         (",".join([str(x) for x in self.
                                    product_variant_ids.ids])))
        data = self._cr.fetchone()
        self.outgoing_picking_reserved_qty = data[0] or 0.0


class ProductProduct(models.Model):

    _inherit = "product.product"

    @api.one
    def _stock_conservative(self):
        pack_stock = 0
        first_subproduct = True
        if self.pack_line_ids:
            for subproduct in self.pack_line_ids:
                subproduct_quantity_next = subproduct.quantity
                if subproduct_quantity_next:
                    result = subproduct.product_id._product_available()[subproduct.product_id.id]
                    subproduct_stock_next = result['qty_available'] - result['outgoing_qty']
                    pack_stock_next = math.floor(subproduct_stock_next / subproduct_quantity_next)
                    if first_subproduct:
                        pack_stock = pack_stock_next
                        first_subproduct = False
                    else:
                        if pack_stock_next < pack_stock:
                            pack_stock = pack_stock_next
            self.virtual_stock_conservative = pack_stock
        else:
            self.virtual_stock_conservative = self.qty_available - self.outgoing_qty - \
                                              self.qty_available_wo_wh - self.qty_available_input_loc
