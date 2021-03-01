from odoo import models, fields, api, _


class RetryAmazonOrders(models.TransientModel):
    _name = 'retry.amazon.orders.wizard'

    @api.multi
    def _get_active_orders(self):
        amazon_orders_obj = self.env['amazon.sale.order']
        amazon_orders_ids = self.env.context.get('active_ids', False)
        wiz_lines=[]
        for order in amazon_orders_obj.search([('id', 'in', amazon_orders_ids)]):
            wiz_lines.append({'amazon_order': order.id})
        return wiz_lines

    amazon_orders = fields.One2many('retry.amazon.orders.lines', "wizard_id", string='Amazon Orders', default=_get_active_orders)

    @api.multi
    def retry_orders(self):
        amazon_orders=self.amazon_orders.mapped('amazon_order')
        amazon_orders.retry_order()
        amazon_orders.process_order()



class RetryAmazonOrdersLines(models.TransientModel):
    _name = 'retry.amazon.orders.lines'

    wizard_id = fields.Many2one('retry.amazon.orders.wizard')
    amazon_order = fields.Many2one('amazon.sale.order', "Amazon Order", readonly=True)

