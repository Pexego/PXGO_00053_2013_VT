from odoo import models, fields, api


class BrandGroup(models.Model):
    _name = 'brand.group'

    name = fields.Char()
    active = fields.Boolean(default=True, help="Set active to false to hide the Brand Group without removing it.")
    brand_ids = fields.One2many('product.brand', 'group_brand_id', string='Brands')
