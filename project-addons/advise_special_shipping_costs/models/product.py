from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    special_shipping_costs = fields.Boolean(related='product_tmpl_id.special_shipping_costs')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    special_shipping_costs = fields.Boolean(string='Special Shipping Costs')


