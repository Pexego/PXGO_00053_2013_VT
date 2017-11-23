# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Visiotech
#    $Jesus Garcia Manzanas <jgmanzanas@visiotechsecurity.com>$
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

from openerp import models, fields, api, _


class CalcCicleSupplierProduct(models.TransientModel):

    _name = "calc.cicle.supplier.product"

    supplier_id = fields.Many2one("res.partner", "Supplier", domain=[('supplier', '=', True)])
    order_cycle = fields.Integer("Order Cicle")

    @api.multi
    def set_cicle_supplier_product(self):
        """Set the cicle of a product depends of the first supplier"""
        product_obj = self.env['product.product']
        purchase_line_obj = self.env['purchase.order.line']
        vals = {'order_cycle': self.order_cycle}
        products_data = purchase_line_obj.read_group([('invoiced', '=', True),
                                                      ('order_id.partner_id', '=', self.supplier_id.id)],
                                                     ['product_id'],
                                                     ['product_id'])
        for product_data in products_data:
            purchase = purchase_line_obj.search([('product_id', '=', product_data['product_id'][0]),
                                                 ('invoiced', '=', True)],
                                                order='id desc', limit=1)
            if self.supplier_id.id == purchase.order_id.partner_id.id:
                product = purchase.product_id
                product.write(vals)