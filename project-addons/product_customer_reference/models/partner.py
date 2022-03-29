from odoo import models, fields, api
from odoo import modules
import base64


class ProductProduct(models.Model):
    _inherit = 'res.partner'

    product_reference_ids = fields.One2many(
        comodel_name='product.customer.reference',
        inverse_name='partner_id',
        string='Product Customer References')



