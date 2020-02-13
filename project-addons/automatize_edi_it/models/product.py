# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    _sql_constraints = [
        ('barcode_uniq', 'check(1=1)',
         "A barcode can only be assigned to one product !"),
        ('default_code_uniq', 'check(1=1)',
         'The code of product must be unique.')
    ]
