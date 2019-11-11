# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, exceptions, _, api
import re


class ProductProduct(models.Model):

    _inherit = "product.product"

    tariff = fields.Float('Tariff', related="product_tmpl_id.hs_code_id.tariff", readonly=True)


class ProductTemplate(models.Model):

    _inherit = "product.template"

    split_method = fields.Selection(selection_add=[('by_tariff',
                                                    'By tariff')])


class HSCode(models.Model):
    _inherit = "hs.code"

    tariff = fields.Float('Tariff', digits=(16, 2))

    @api.constrains('local_code')
    def check_hs_code(self):
        for code in self:
            if not re.match('^[0-9]{6}([0-9])?([0-9])?(\.[0-9])?([0-9])?$', code.local_code):
                message = _('The HS Code format is incorrect')
                raise exceptions.ValidationError(message)
