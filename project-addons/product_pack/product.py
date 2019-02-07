# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015-2016 Comunitea Servicios Tecnológicos
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
#    $Omar Castiñeira saavedra <omar@comunitea.com>$
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
from odoo import fields, models, api
from collections import Counter


class product_pack(models.Model):
    _name = 'product.pack.line'
    _rec_name = 'product_id'

    parent_product_id = fields.Many2one(
            'product.product', 'Parent Product',
            ondelete='cascade', required=True)
    quantity = fields.Float('Quantity', required=True)
    product_id = fields.Many2one(
            'product.product', 'Product', required=True)

    def update_pack_products(self, cr, uid, ids, context=None):
        for update_line in self.browse(cr, uid, ids):
            cost_price = 0.0
            for pack_line in update_line.parent_product_id.pack_line_ids:
                cost_price += (pack_line.product_id.standard_price *
                               pack_line.quantity)
            update_line.parent_product_id.write({'standard_price': cost_price})
        return True

    def create(self, cr, uid, vals, context=None):
        res = super(product_pack, self).create(cr, uid, vals, context=context)
        self.update_pack_products(cr, uid, [res], context=context)
        return res

    def write(self, cr, uid, ids, vals, context):
        res = super(product_pack, self).write(cr, uid, ids, vals,
                                              context=context)
        self.update_pack_products(cr, uid, ids, context=context)
        return res


class product_product(models.Model):
    _inherit = 'product.product'

    #TODO: Migrar si no se opta por mrp_om_phantom_fix
    # ~ def _product_available(self, cr, uid, ids, field_names=None, arg=False,
                           # ~ context=None):
        # ~ res = {}
        # ~ for product in self.browse(cr, uid, ids, context=context):
            # ~ stock = super(product_product, self)._product_available(
                # ~ cr, uid, [product.id], field_names, arg, context)

            # ~ if not product.stock_depends:
                # ~ res[product.id] = stock[product.id]
                # ~ continue

            # ~ first_subproduct = True
            # ~ pack_stock = 0
            # ~ pack_available = 0
            # ~ pack_incoming = 0
            # ~ pack_outgoing = 0

            # ~ # Check if product stock depends on it's subproducts stock.
            # ~ if product.pack_line_ids:
                # ~ """ Go over all subproducts, take quantity needed for the pack
                # ~ and its available stock """
                # ~ for subproduct in product.pack_line_ids:

                    # ~ # if subproduct is a service don't calculate the stock
                    # ~ if subproduct.product_id.type == 'service':
                        # ~ continue
                    # ~ if first_subproduct:
                        # ~ subproduct_quantity = subproduct.quantity
                        # ~ if subproduct_quantity == 0:
                            # ~ continue
                        # ~ result = self.\
                            # ~ _product_available(cr, uid,
                                               # ~ [subproduct.product_id.id],
                                               # ~ field_names, arg, context)
                        # ~ subproduct_stock = result[subproduct.product_id.id]
                        # ~ subproduct_available = \
                            # ~ subproduct_stock['qty_available']
                        # ~ subproduct_virtual = \
                            # ~ subproduct_stock['virtual_available']
                        # ~ subproduct_incoming = subproduct_stock['incoming_qty']
                        # ~ subproduct_outgoing = subproduct_stock['outgoing_qty']

                        # ~ """ Calculate real stock for current pack from the
                        # ~ subproduct stock and needed quantity """
                        # ~ pack_stock = math.floor(
                            # ~ subproduct_available / subproduct_quantity)
                        # ~ pack_available = math.floor(
                            # ~ subproduct_virtual / subproduct_quantity)
                        # ~ pack_incoming = math.floor(
                            # ~ subproduct_incoming / subproduct_quantity)
                        # ~ pack_outgoing = math.floor(
                            # ~ subproduct_outgoing / subproduct_quantity)
                        # ~ first_subproduct = False
                        # ~ continue

                    # ~ # Take the info of the next subproduct
                    # ~ subproduct_quantity_next = subproduct.quantity
                    # ~ if (
                        # ~ subproduct_quantity_next == 0
                        # ~ or subproduct_quantity_next == 0.0
                    # ~ ):
                        # ~ continue
                    # ~ result2 = self.\
                        # ~ _product_available(cr, uid, [subproduct.product_id.id],
                                           # ~ field_names, arg,
                                           # ~ context)[subproduct.product_id.id]
                    # ~ subproduct_stock_next = result2['qty_available']
                    # ~ subproduct_virtual_next = result2['virtual_available']
                    # ~ subproduct_incoming_next = result2['incoming_qty']
                    # ~ subproduct_outgoing_next = result2['outgoing_qty']

                    # ~ pack_stock_next = math.floor(
                        # ~ subproduct_stock_next / subproduct_quantity_next)
                    # ~ pack_available_next = math.floor(
                        # ~ subproduct_virtual_next / subproduct_quantity_next)
                    # ~ pack_incoming_next = math.floor(
                        # ~ subproduct_incoming_next / subproduct_quantity_next)
                    # ~ pack_outgoing_next = math.floor(
                        # ~ subproduct_outgoing_next / subproduct_quantity_next)

                    # ~ # compare the stock of a subproduct and the next subproduct
                    # ~ if pack_stock_next < pack_stock:
                        # ~ pack_stock = pack_stock_next
                    # ~ if pack_available_next < pack_available:
                        # ~ pack_available = pack_available_next
                    # ~ if pack_incoming_next < pack_incoming:
                        # ~ pack_incoming = pack_incoming_next
                    # ~ if pack_outgoing_next < pack_outgoing:
                        # ~ pack_outgoing = pack_outgoing_next

                # ~ # result is the minimum stock of all subproducts
                # ~ res[product.id] = {
                    # ~ 'qty_available': pack_stock,
                    # ~ 'incoming_qty': pack_incoming,
                    # ~ 'outgoing_qty': pack_outgoing,
                    # ~ 'virtual_available': pack_available,
                # ~ }
            # ~ else:
                # ~ res[product.id] = stock[product.id]
        # ~ return res

    # ~ def _search_product_quantity(self, cr, uid, obj, name, domain, context):
        # ~ return super(product_product, self).\
            # ~ _search_product_quantity(cr, uid, obj, name, domain, context)

    stock_depends = fields.Boolean(
            'Stock depends of components', default=True,
            help='Mark if pack stock is calcualted from component stock')
    pack_fixed_price = fields.Boolean(
            'Pack has fixed price', default=True,
            help="""
            Mark this field if the public price of the pack should be fixed.
            Do not mark it if the price should be calculated from the sum of
            the prices of the products in the pack.
        """)
    pack_line_ids = fields.One2many(
            'product.pack.line', 'parent_product_id', 'Pack Products',
            help='List of products that are part of this pack.')
    #TODO: Migrar
        # ~ 'qty_available': fields.
        # ~ function(_product_available, multi='qty_available',
                 # ~ type='float',
                 # ~ digits=
                 # ~ dp.get_precision('Product Unit of Measure'),
                 # ~ string='Quantity On Hand',
                 # ~ fnct_search=_search_product_quantity,
                 # ~ help="Current quantity of products.\n"
                      # ~ "In a context with a single Stock Location, this "
                      # ~ "includes goods stored at this Location, or any of its "
                      # ~ "children.\nIn a context with a single Warehouse, this "
                      # ~ "includes goods stored in the Stock Location of this "
                      # ~ "Warehouse, or any of its children.\n"
                      # ~ "Stored in the Stock Location of the Warehouse of this "
                      # ~ "Shop, or any of its children.\n"
                      # ~ "Otherwise, this includes goods stored in any Stock "
                      # ~ "Location with 'internal' type."),
        # ~ 'virtual_available': fields.
        # ~ function(_product_available, multi='qty_available', type='float',
                 # ~ digits=dp.get_precision('Product Unit of Measure'),
                 # ~ string='Forecast Quantity',
                 # ~ fnct_search=_search_product_quantity,
                 # ~ help="Forecast quantity (computed as Quantity On Hand "
                 # ~ "- Outgoing + Incoming)\n"
                 # ~ "In a context with a single Stock Location, this includes "
                 # ~ "goods stored in this location, or any of its children.\n"
                 # ~ "In a context with a single Warehouse, this includes "
                 # ~ "goods stored in the Stock Location of this Warehouse, or "
                 # ~ "any of its children.\n"
                 # ~ "Otherwise, this includes goods stored in any Stock Location "
                 # ~ "with 'internal' type."),
        # ~ 'incoming_qty': fields.
        # ~ function(_product_available, multi='qty_available', type='float',
                 # ~ digits=dp.get_precision('Product Unit of Measure'),
                 # ~ string='Incoming', fnct_search=_search_product_quantity,
                 # ~ help="Quantity of products that are planned to arrive.\n"
                 # ~ "In a context with a single Stock Location, this includes "
                 # ~ "goods arriving to this Location, or any of its children.\n"
                 # ~ "In a context with a single Warehouse, this includes "
                 # ~ "goods arriving to the Stock Location of this Warehouse, or "
                 # ~ "any of its children.\n"
                 # ~ "Otherwise, this includes goods arriving to any Stock "
                 # ~ "Location with 'internal' type."),
        # ~ 'outgoing_qty': fields.
        # ~ function(_product_available, multi='qty_available', type='float',
                 # ~ digits=dp.get_precision('Product Unit of Measure'),
                 # ~ string='Outgoing', fnct_search=_search_product_quantity,
                 # ~ help="Quantity of products that are planned to leave.\n"
                 # ~ "In a context with a single Stock Location, this includes "
                 # ~ "goods leaving this Location, or any of its children.\n"
                 # ~ "In a context with a single Warehouse, this includes "
                 # ~ "goods leaving the Stock Location of this Warehouse, or "
                 # ~ "any of its children.\n"
                 # ~ "Otherwise, this includes goods leaving any Stock "
                 # ~ "Location with 'internal' type."),

    # def write(self, cr, uid, ids, vals, context=None):
    #     pack_lines_to_update = []
    #     if 'standard_price' in vals:
    #         for prod in self.browse(cr, uid, ids, context=context):
    #             if vals['standard_price'] != prod.standard_price:
    #                 pline_ids = self.pool.get('product.pack.line').\
    #                     search(cr, uid, [('product_id', '=', prod.id)])
    #                 if pline_ids:
    #                     pack_lines_to_update.extend(pline_ids)
    #     res = super(product_product, self).write(cr, uid, ids, vals,
    #                                              context=context)
    #     if pack_lines_to_update:
    #         self.pool.get('product.pack.line').\
    #             update_pack_products(cr, uid, pack_lines_to_update,
    #                                  context=context)
    #     return res

    @api.multi
    def get_pack(self):
        pack = Counter({})
        if not self.pack_line_ids:
            return {}
        for line in self.pack_line_ids:
            if line.product_id.pack_line_ids:
                line_pack = line.product_id.get_pack()
                pack += Counter({x: line_pack[x] * line.quantity for x in line_pack})
            else:
                pack[line.product_id.id] = line.quantity
        return dict(pack)
