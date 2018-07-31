# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class ProductProduct(models.Model):

    _inherit = "product.product"

    @api.multi
    def name_get(self):

        self = self.with_context(display_default_code=False)
        result = super(ProductProduct, self).name_get()

        return result
