# -*- coding: utf-8 -*-

from openerp import fields, models, api, _

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def get_customizable_products(self):
        tags = self.env['product.tag']
        tag_code = tags.search([('name', '=', 'Personalizable')]).id
        product_object = self.env['product.product']
        product = product_object.search([('tag_ids', '=', tag_code)])

        ids_products = [x.id for x in product]
        return {
            'domain': "[('id','in', " + str(ids_products) + ")]",
            'name': _('Customizable Products'),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': {'tree_view_ref': 'product.product_product_tree_view',
                        'readonly_by_pass': ['lst_price', 'list_price2', 'list_price3', 'list_price4']},
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
        }