from odoo import models, fields, _, exceptions, api


class AutomaticCustomizationTypeRule(models.Model):
    _name = 'automatic.customization.type.rule'

    product_brand_id = fields.Many2one('product.brand', string="Product Brand")
    product_categ_id = fields.Many2one('product.category', string="Product Category")
    type_id = fields.Many2one('customization.type')
