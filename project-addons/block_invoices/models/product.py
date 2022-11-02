from odoo import models, fields, exceptions, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    exclude_margin = fields.Boolean()



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def write(self, vals):
        for product in self:
            if vals.get('state', False) and vals.get('state') == 'end':
                product.product_variant_ids.write({'exclude_margin': True})
        return super(ProductTemplate, self).write(vals)
