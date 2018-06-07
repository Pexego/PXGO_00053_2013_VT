from openerp import models, fields, api


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    orders = fields.Char('Orders', compute='get_orders', readonly=True, store=True)

    @api.multi
    @api.depends('invoice_line')
    def get_orders(self):
        orders = ''
        for invoice in self:
            for order in invoice.sale_order_ids:
                if orders.find(order.name) == -1:
                    orders += order.name + ','
            if orders.endswith(','):
                self.orders = orders[:-1]
