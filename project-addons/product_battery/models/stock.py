from odoo import fields, models


class StockMove(models.Model):

    _inherit = 'stock.move'

    battery_id = fields.Many2one(related='product_id.battery_id', readonly=True)
