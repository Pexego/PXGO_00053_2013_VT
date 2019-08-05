from odoo import fields, models


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    battery_id = fields.Many2one('product.battery', 'Battery Type')
