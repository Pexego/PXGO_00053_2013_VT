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


class sale_equivalent_products(orm.TransientModel):

    _name = "sale.equivalent.products"
    _description = "Wizard for change products in sale order line"

    def _get_products(self, cr, uid, ids, field_name, arg, context=None, tag_ids=None):
        res = {}
        product_obj = self.pool.get('product.product')
        tag_obj = self.pool.get('product.tag')
        tag_wiz_obj = self.pool.get('sale.equivalent.tag')
        for wiz in self.browse(cr, uid, ids, context):
            if not tag_ids:
                tag_ids = [x.id for x in wiz.tag_ids]
            product_ids = set(product_obj.search(cr, uid, [('sale_ok', '=', True)], context=context))
            # se buscan todos los product.tag que coincidan con los del wiz
            for tag in tag_wiz_obj.browse(cr, uid, tag_ids, context):
                tag_ids = tag_obj.search(cr, uid, [('name', '=', tag.name)], context=context)
                products = product_obj.search(cr, uid, [('tag_ids', 'in', tag_ids), ('sale_ok', '=', True)], context=context)
                product_ids = product_ids and set(products)
            res[wiz.id] = list(product_ids)
        return res

    _columns = {
        'line_id': fields.many2one('sale.order.line','Line'),
        'tag_ids': fields.one2many('sale.equivalent.tag', 'wiz_id', 'Tags'),
        'product_ids': fields.function(_get_products, type='one2many', relation='product.product', string='Products'),
    }

    def onchange_tags(self, cr, uid, ids, tag_ids=False, context=None):
        if not tag_ids:
            return True
        tag_ids = tag_ids[0][2]
        product_ids = self._get_products(cr, uid, ids, "", "", context, tag_ids)
        return {'value': {'product_ids': product_ids[ids[0]]}}


class sale_equivalent_tag(orm.TransientModel):

    _name = "sale.equivalent.tag"
    _description = "Tags for equivalent products wizard"

    _columns = {
        'wiz_id': fields.many2one('sale.equivalent.products', 'Wizard'),
        'name': fields.char('Name', size=64),
    }

