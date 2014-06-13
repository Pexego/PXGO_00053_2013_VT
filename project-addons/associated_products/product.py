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
from openerp.tools.translate import _


class product(orm.Model):

    _inherit = "product.product"

    _columns = {
        'associated_product_ids': fields.one2many('product.associated',
                                                  'product_id',
                                                  'Associated products'),
    }


class associated_products(orm.Model):

    _name = "product.associated"
    _description = "This model provides the association between a \
        product an their associated products"

    _parent_name = "product_id"
    _parent_store = True

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'associated_id': fields.many2one('product.product',
                                         'Associated product', required=True),
        'quantity': fields.float('Quantity', required=True),
        'uom_id': fields.many2one('product.uom', 'UoM', required=True),
    }

    _constraints = [
        (orm.Model._check_recursion,
         'Error ! You cannot create recursive tags.', ['parent_id'])
    ]

    """def create(self, cr, uid, vals, context=None):
        assoc_id = super(associated_products,self).create(cr, uid, vals, context)
        assoc = self.browse(cr, uid, assoc_id, context)
        if assoc.product_id == assoc.associated_id:
            raise orm.except_orm(_('Recursive error'), _('Error ! You cannot create recursive associations.'))
        if assoc
        return assoc_id

    def write(self, cr, uid, ids, vals, context=None):
        ok = super(associated_products,self).write(cr, uid, ids, vals, context)
        for associated in self.browse(cr, uid, ids, context):
            if associated.product_id.id == associated.associated_id.id:
                raise orm.except_orm(_('Recursive error'), _('Error ! You cannot create recursive associations.'))
        return ok"""


