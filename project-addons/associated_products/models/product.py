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

from odoo import fields, models, api

class Product(models.Model):

    _inherit = 'product.product'

    associated_product_ids = fields.One2many('product.associated', 'product_id', "Associated products")
    equivalent_product_ids = fields.One2many('product.equivalent',  'product_id', "Equivalent products")
    equivalent_products = fields.One2many('product.product',compute="_compute_equivalent_products",search="_search_equivalent_products")

    def _compute_equivalent_products(self):
        """
            This method compute equivalent products of a product.
        :return: products with default_code like value and products equivalents whose product_name like value
        """
        for product in self:
            prod_equiv = self.env['product.equivalent'].search(['|',('product_id', '=', product.id),('equivalent_id', '=', product.id)])
            if not prod_equiv:
                products = product
            else:
                products = prod_equiv.mapped('product_id') + prod_equiv.mapped('equivalent_id')
            product.equivalent_products = products

    def _search_equivalent_products(self, operator, value):
        """
            This method allows you to search Equivalent Products.
        :return: products with default_code like value and products equivalents whose product_name like value
        """
        prod_equiv = self.env['product.equivalent'].search(['|',('product_id.default_code', operator, value),('product_name', operator, value)])
        if not prod_equiv:
            products = self.env['product.product'].search([('default_code', operator, value)])
        else:
            products = prod_equiv.mapped('product_id') + prod_equiv.mapped('equivalent_id')
        return [('id', 'in', products.ids)]


class AssociatedProducts(models.Model):

    _name = 'product.associated'
    _description = "This model provides the association between a product and their associated products"

    @api.multi
    def _get_default_uom_id(self):
        return self.env.ref('product.product_uom_unit').id

    product_id = fields.Many2one('product.product', "Product", required=True)
    associated_id = fields.Many2one('product.product', "Associated product", required=True)
    quantity = fields.Float("Quantity", required=True)
    uom_id = fields.Many2one('product.uom', "UoM", required=True, default=_get_default_uom_id)
    discount = fields.Float("Discount (%)", required=True, default=0)


class EquivalentProduct(models.Model):

    _name = 'product.equivalent'

    product_id = fields.Many2one('product.product', "Product", required=True)
    equivalent_id = fields.Many2one('product.product', "Equivalent product")
    product_name = fields.Char()

    _sql_constraints = [
        ('product_equivalent_uniq', 'unique(product_id, equivalent_id, product_name)',
         'There is already an equivalent product for this product'),
    ]

    @api.model
    def create(self, vals):
        """
            This method create the equivalent product and its inverse relation
        :return: Super return
        """
        res = super(EquivalentProduct, self).create(vals)
        product = self.env['product.product'].browse(vals.get('product_id'))
        equivalent_id = vals.get('equivalent_id')
        if product and equivalent_id:
            product_equiv = self.env['product.equivalent'].search([('product_id','=',equivalent_id),('equivalent_id','=',product.id)])
            if not product_equiv:
                vals_rev = {'equivalent_id': product.id, 'product_id': equivalent_id, 'product_name':product.default_code}
                self.env['product.equivalent'].create(vals_rev)
        return res

    @api.multi
    def unlink(self):
        """
            This method allows you to unlink inverse equivalent product
        :return: Super return
        """
        products=self
        for product in products:
            product_equiv = self.env['product.equivalent'].search(
                [('product_id', '=', product.equivalent_id.id), ('equivalent_id', '=', product.product_id.id)])
            if product_equiv:
                products |= product_equiv
        return super(EquivalentProduct, products).unlink()

    def action_open_product_equivalent(self):
        """
            This method allows you to open an Equivalent Product View
        :return: Action to show the view
        """
        action = self.env.ref('product.product_template_action')
        result = action.read()[0]
        result['context'] = {}
        res = self.env.ref('product.product_normal_form_view', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = self.equivalent_id.id
        return result
