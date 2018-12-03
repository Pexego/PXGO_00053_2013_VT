from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    sale_in_groups_of = fields.Float('Sale in groups of', default=1.0)






