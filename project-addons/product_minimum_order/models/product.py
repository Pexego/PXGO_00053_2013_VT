# -*- coding: utf-8 -*-

from openerp import models, fields, api

class product_product(models.Model):
    _inherit = 'product.product'

    sale_in_groups_of = fields.Float('Sale in groups of', default=1.0)






