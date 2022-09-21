from odoo import models, fields

class ProductBrand(models.Model):

    _inherit = 'product.brand'

    category_ids = fields.Many2many('res.partner.category', string='Allow Partner Categories')


