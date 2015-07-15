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

    @api.constrains('state', 'amount_shipping_balance', 'amount_untaxed')
    def _check_amount_on_state(self):
        if self.amount_untaxed < 0:
            raise ValidationError("Total amount must be > 0")


    @api.multi
    def unlink(self):

        res = sale_order._action_unlink_shipping(self)

        if res:
            return super(sale_order, self).unlink()


    @api.multi
    def action_cancel(self, group=False):
        # import ipdb; ipdb.set_trace()
        res = super(sale_order, self).action_cancel()
        if res:
            return sale_order._action_unlink_shipping(self)

    @api.one
    def _action_unlink_shipping(self):

        #res_id = self.id
        #order_line = self.env['sale.order.line'].search(
        #    [('order_id', '=', res_id), ('product_id.shipping_balance', '=', True)])
        #if order_line:
        #    order_line.unlink()
        line2 = self.env['shipping.balance'].search([('sale_id', '=', self.id)])
        if line2:
            line2.unlink()
        return True


class sale_order_line(models.Model):

    _inherit = "sale.order.line"

    @api.multi
    def unlink(self):
        import ipdb; ipdb.set_trace()
        res_id= self.order_id.id

        res = super(sale_order_line, self).unlink()
        line2 = self.env['shipping.balance'].search([('sale_id', '=', res_id)])
        if line2:
            line2.unlink()
        return True

    @api.constrains('price_unit')
    def _check_description(self):
        old_value = self.env['shipping.balance'].search([('sale_id', '=', self.order_id.id)]).amount
        old_line_value = self.env['sale.order.line'].search([('id', '=', self.id)]).price_unit

        amount_untaxed = self.order_id.amount_untaxed - old_line_value + self.price_unit
        if amount_untaxed <0:
            raise ValidationError("Total amount must be > 0")
        if self.product_id.shipping_balance:
            if self.price_unit > 0:
                raise ValidationError("Price unit must be < 0. (Discount)")

            if (self.order_id.amount_shipping_balance - old_value + self.price_unit) < 0:
                raise ValidationError("Not enough Shipping Balance.")

            self.env['shipping.balance'].search([('sale_id', '=', self.order_id.id)]).write({'amount': self.price_unit})
