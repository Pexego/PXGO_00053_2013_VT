# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class ProductBrand(models.Model):

    _inherit = 'product.brand'

    code = fields.Char('Internal code')
    not_compute_joking = fields.Boolean('Not compute joking index')


class ProductCategory(models.Model):

    _inherit = 'product.category'

    code = fields.Char('Internal code')