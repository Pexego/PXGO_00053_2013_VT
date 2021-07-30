from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    asin_code = fields.Char("Amazon ASIN", copy=False)
