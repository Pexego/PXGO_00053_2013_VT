# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sanchez <kiko@comunitea.com>$
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
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import models, fields, api, exceptions
from datetime import date
from openerp.exceptions import ValidationError

class sale_order(models.Model):

    _inherit = "sale.order"
    shipping_balance = fields.Boolean('shipping_balance')
    amount_shipping_balance=fields.Float(related='partner_id.amount_shipping_balance')


    @api.constrains('state')
    def _check_amount_on_state(self):
        if self.amount_untaxed < 0:
            raise ValidationError("Total amount must be > 0")


    @api.multi
    def create_shipping_line(self):
        import ipdb; ipdb.set_trace()
        sale_order_pool = self.env['sale.order']
        sale_order_line_pool = self.env['sale.order.line']
        product_pool = self.env['product.product']
        product=product_pool.search([('shipping_balance', '=', "true")])[0]
        new_line_vals = {
            'order_id' : self.id,
            'product_id' : product.id,
            'price_unit' : -self.partner_id.amount_shipping_balance,
            'product_uom_qty' : 1,
            'name' : product.name
        }
        sale_order_line_pool.create(new_line_vals)
        return True




class sale_order_line(models.Model):

    _inherit = "sale.order.line"

    @api.multi
    def unlink(self):

        res_id= self.order_id.id
        line2 = self.env['shipping.balance'].search([('sale_id', '=', res_id)])
        if line2:
            line2.unlink()
        return True

    @api.constrains('price_unit')
    def _check_description(self):
        if self.product_id.shipping_balance:
            if self.price_unit < -self.order_id.partner_id.amount_shipping_balance:
                raise ValidationError("Price < Shipping Balance")

            if self.price_unit > 0:
                raise ValidationError("Price unit must be < 0. (Discount)")

