# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class ProductBrand(models.Model):

    _inherit = 'product.brand'

    code = fields.Char('Internal code')


class ProductCategory(models.Model):

    _inherit = 'product.category'

    code = fields.Char('Internal code')
    percent = fields.Integer(string="Percent",
                             help="This percent will be used when a product moves to an outlet category")

    # ean13 = fields.Char('EAN13', size=13)

    @api.one
    @api.constrains('percent')
    def check_length(self):
        percent = self.percent
        if (percent > 100) | (percent < 0):
            raise exceptions. \
                ValidationError(_('Error ! The percent values must be between 0 and 100'))
        return True
