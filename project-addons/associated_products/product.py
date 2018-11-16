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

from openerp.osv import fields, orm
from openerp import models, api, fields as fields2


class product(orm.Model):

    _inherit = "product.product"

    _columns = {
        'associated_product_ids': fields.one2many('product.associated',
                                                  'product_id',
                                                  'Associated products'),
        'equivalent_product_ids': fields.one2many('product.equivalent',
                                                  'product_id',
                                                  'Equivalent products'),
    }


class associated_products(orm.Model):

    _name = "product.associated"
    _description = "This model provides the association between a \
        product and their associated products"

    def _get_default_uom_id(self):
        return self.env.ref('product.product_uom_unit').id

    _columns = {
        'product_id': fields.many2one('product.product', 'Product',
                                      required=True),
        'associated_id': fields.many2one('product.product',
                                         'Associated product', required=True),
        'quantity': fields.float('Quantity', required=True),
        'uom_id': fields.many2one('product.uom', 'UoM', required=True, default=_get_default_uom_id),
        'discount': fields.float('Discount (%)', required=True, default=0)
    }


class EquivalentProduct(models.Model):

    _name = 'product.equivalent'

    product_id = fields2.Many2one('product.product', 'Product', required=True)
    equivalent_id = fields2.Many2one('product.product', 'Equivalent product', required=True)
