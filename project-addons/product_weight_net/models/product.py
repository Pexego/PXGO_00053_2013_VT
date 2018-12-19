from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    weight_net = fields.Float('Net Weight', digits_compute=dp.get_precision('Stock Weight'),
                              help="The net weight in Kg")
