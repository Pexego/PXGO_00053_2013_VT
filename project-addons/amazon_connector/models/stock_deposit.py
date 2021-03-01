from odoo import models, fields, api


class StockDeposit(models.Model):
    _inherit = 'stock.deposit'

    amazon_order_id = fields.Many2one("amazon.sale.order")