from odoo import models, fields, api


class BrandGroup(models.Model):
    _name = 'brand.group'

    name = fields.Char()
    active = fields.Boolean(default=True, help="Set active to false to hide the Brand Group without removing it.")
    brand_ids = fields.Many2many('product.brand',
                                 relation="brand_group_product_brand_rel", column1='brand_group_id',
                                 column2='product_brand_id', string='Brands')
