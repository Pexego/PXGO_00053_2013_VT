# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductProduct(models.Model):

    _inherit = "product.product"

    tariff = fields.Float('Tariff', digits=(16, 2))


class ProductTemplate(models.Model):

    _inherit = "product.template"

    split_method = fields.Selection(selection_add=[('by_tariff',
                                                    'By tariff')])
