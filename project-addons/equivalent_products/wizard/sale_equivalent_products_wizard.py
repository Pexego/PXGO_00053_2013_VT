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

    def _get_products(self, cr, uid, ids, field_name, arg, context=None,
                      tag_ids=None, onchange=None):
        res = {}
        product_obj = self.pool.get('product.product')
        tag_obj = self.pool.get('product.tag')
        tag_wiz_obj = self.pool.get('sale.equivalent.tag')
        for wiz in self.browse(cr, uid, ids, context):
            if not onchange:
                tag_ids = [x.id for x in wiz.tag_ids]
            product_ids = set(product_obj.search(cr, uid,
                                                 [('sale_ok', '=', True)],
                                                 context=context))
            # se buscan todos los product.tag que coincidan con los del wiz
            for tag in tag_wiz_obj.browse(cr, uid, tag_ids, context):
                tag_ids = tag_obj.search(cr, uid,
                                         [('name', '=', tag.name)],
                                         context=context)
                products = product_obj.search(cr, uid,
                                              [('tag_ids', 'in', tag_ids),
                                               ('sale_ok', '=', True)],
                                              context=context)
                product_ids = product_ids & set(products)
            res[wiz.id] = list(product_ids)
        return res

    _columns = {
        'line_id': fields.many2one('sale.order.line', 'Line'),
        'tag_ids': fields.one2many('sale.equivalent.tag', 'wiz_id', 'Tags'),
        'product_ids': fields.function(_get_products, type='one2many',
                                       relation='product.product',
                                       string='Products'),
        'product_id': fields.many2one('product.product', 'Product selected'),
    }

    def onchange_tags(self, cr, uid, ids, tag_ids=False, context=None):
        if not tag_ids:
            return True
        tag_ids = tag_ids[0][2]
        product_ids = self._get_products(cr, uid, ids,
                                         "product_ids", "",
                                         context, tag_ids,
                                         True)[ids[0]]
        return {'value': {'product_ids': product_ids},
                'domain': {'product_id': [('id', 'in', product_ids)]}}

    def select_product(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0], context)

        # borrar el if al arreglar el domain
        if wiz.product_id.id not in [x.id for x in wiz.product_ids]:
            raise orm.except_orm(_('Error'),
                                 _('El producto no es equivalente'))
        order_line_obj = self.pool.get('sale.order.line')
        order_line_obj.write(cr, uid,
                             wiz.line_id.id,
                             {'product_id': wiz.product_id.id}, context)
        line_vals = order_line_obj.product_id_change(cr, uid, wiz.line_id.id, wiz.line_id.order_id.pricelist_id.id, wiz.product_id.id, wiz.line_id.product_uom_qty, False, wiz.line_id.product_uos_qty, False, wiz.line_id.name, wiz.line_id.order_id.partner_id, False, True, wiz.line_id.order_id.date_order, False, wiz.line_id.order_id.fiscal_position, False, context)
        # TODO: probar que funciona bien
        line_vals = line_vals['value']
        order_line_obj.write(cr, uid,
                             wiz.line_id.id, line_vals, context)

class sale_equivalent_tag(orm.TransientModel):

    _name = "sale.equivalent.tag"
    _description = "Tags for equivalent products wizard"

    _columns = {
        'wiz_id': fields.many2one('sale.equivalent.products', 'Wizard'),
        'name': fields.char('Name', size=64),
    }
