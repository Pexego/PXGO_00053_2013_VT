from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ShipBalanWzd(models.TransientModel):

    _name = 'shipping.balance.wizard'

    amount_ok = fields.Float(
        'Shipping Balance OK',
        default=lambda self:
        self.env['sale.order'].browse(self.env.context["active_ids"][0]).partner_id.amount_shipping_balance)

    @api.constrains('amount_ok')
    def _check_amount_ok(self):
        if self.amount_ok <= 0:
            raise ValidationError("Shipping Balance must be > 0")
        if self.amount_ok - self.env['sale.order'].browse(self.env.context["active_ids"][0]).partner_id.amount_shipping_balance > 0:
            raise ValidationError("Shipping Balance must > apartner shipping")

    @api.multi
    def create_shipping_line_ok(self):

        if self.amount_ok > 0:
            sale_order_pool = self.env['sale.order']
            sale_order_line_pool = self.env['sale.order.line']
            product_pool = self.env['product.product']
            self1 = sale_order_pool.browse(self.env.context["active_ids"][0])
            product = product_pool.search([('shipping_balance', '=', "true")])[0]
            new_line_vals = {
                'order_id': self1.id,
                'product_id': product.id,
                'price_unit': -self.amount_ok,
                'product_uom_qty': 1,
                'name': product.name
                }
            e=sale_order_line_pool.search([('price_unit', "<", 0), ('order_id', "=", self1.id)])
            if not e:
                sale_order_line_pool.create(new_line_vals)
            else:
                e.write(new_line_vals)

            shipping_vals = {
                   'partner_id': self1.partner_id.id,
                   'sale_id': self1.id,
                   'aproved_ok': True,
                   'amount': -self.amount_ok,
                   'balance': False,

                   }
            line2 = self.env['shipping.balance'].search([('sale_id', '=', self1.id)])
            if line2:
                line2.write(shipping_vals)

            else:
                self.env['shipping.balance'].create(shipping_vals)

        return True
