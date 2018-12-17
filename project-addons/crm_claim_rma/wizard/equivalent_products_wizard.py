# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from odoo import fields, models


class equivalent_products_wizard(models.TransientModel):

    _name = "equivalent.products.wizard"
    _description = "Wizard for change products in claim."

    product_tag_ids = fields.Many2many("product.tag",
                                    "product_tag_wzf_equivalent_rel",
                                    "wizard_id", "tag_id", "Tags")
    product_id = fields.Many2one('product.product', 'Product selected')
    line_id = fields.Many2one('claim.line', 'Line')
    real_stock = fields.Float("Real Stock", readonly=True)
    virtual_stock = fields.Float("Virtual Stock", readonly=True)

    def default_get(self, cr, uid, fields, context=None):
        res = super(equivalent_products_wizard, self).default_get(cr, uid, fields, context=context)
        if context.get('line_id'):
            claim_line_id = self.pool.get('claim.line').browse(cr, uid, context['line_id'])
            res['product_id'] = claim_line_id.product_id.id
            res['real_stock'] = claim_line_id.product_id.qty_available
            res['virtual_stock'] = claim_line_id.product_id.virtual_available
            res['product_tag_ids'] = \
                [(6, 0, claim_line_id.product_id.tag_ids.ids)]
        return res

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        if not product_id:
            return {}
        prod_obj = self.pool.get('product.product')
        prod_id = prod_obj.browse(cr, uid, product_id)
        virtual_stock = prod_id.virtual_available
        real_stock = prod_id.qty_available
        return {
            'value': {'virtual_stock': virtual_stock,
                      'real_stock': real_stock}
        }

    def select_product(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0], context)

        order_line_obj = self.pool.get('claim.line')
        order_line_obj.write(cr, uid,
                             [wiz.line_id.id],
                             {'equivalent_product_id': wiz.product_id.id},
                             context)

