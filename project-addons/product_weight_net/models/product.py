from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = 'product.product'

    weight = fields.Float('Gross Weight', digits_compute=dp.get_precision('Stock Weight'),
                          help="The gross weight in Kg.")
    weight_net = fields.Float('Net Weight', digits_compute=dp.get_precision('Stock Weight'),
                              help="The net weight in Kg.")

