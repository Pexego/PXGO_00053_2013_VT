from odoo import models, fields, api


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    orders = fields.Char('Orders', compute='get_orders', readonly=True, store=False)

    @api.multi
    def get_orders(self):
        for invoice in self:
            orders = ''
            for order in invoice.sale_order_ids:
                orders += order.name + ','
            if orders.endswith(','):
                self.orders = orders[:-1]
