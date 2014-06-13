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


class sale_order_line(orm.Model):

    _inherit = "sale.order.line"

    # la llamada recursiva falla
    """def create_associated_line(self, cr, uid, product, flag=False, qty=0.0, uom_id=None, order_id=None, context=None):
        import pdb; pdb.set_trace()
        for associated in product.associated_product_ids:
            self.create_associated_line(cr, uid, associated.associated_id, True, associated.quantity, associated.uom_id.id, order_id, context)
        if flag:
            args_line = {
                'order_id': order_id,
                'product_uom': uom_id,
                'product_uom_qty': qty,
                'product_id': product.id,
            }
            line_assoc_id = self.pool.get('sale.order.line').create(cr, uid, args_line, context)

    def create(self, cr, uid, vals, context=None):
        product_obj = self.pool.get('product.product')
        line_obj = self.pool.get('sale.order.line')
        product_id = vals.get('product_id')
        line_id = super(sale_order_line,self).create(cr, uid, vals, context)
        line = line_obj.browse(cr, uid, line_id, context)
        if product_id:
            product = product_obj.browse(cr, uid, product_id, context)
            self.create_associated_line(cr, uid, product, order_id=line.order_id.id, context=context)

        return line_id"""

