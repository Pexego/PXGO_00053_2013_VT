# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
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
import openerp
from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
        'qty_reserved': fields.float('Qty reserved', readonly=True,
                                     digits_compute=
                                     dp.get_precision('Product Unit \
                                                      of Measure'))
    }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None):
        result = super(sale_order_line,
                       self).product_id_change(cr, uid, ids, pricelist,
                                               product, qty, uom, qty_uos, uos,
                                               name, partner_id, lang,
                                               update_tax, date_order,
                                               packaging, fiscal_position,
                                               flag, context)
        context = context or {}
        product_obj = self.pool.get('product.product')
        partner_obj = self.pool.get('res.partner')
        lang = lang or context.get('lang', False)
        context = {'lang': lang, 'partner_id': partner_id}
        partner = partner_obj.browse(cr, uid, partner_id)
        lang = partner.lang
        context_partner = {'lang': lang, 'partner_id': partner_id}
        if product:
            product = product_obj.browse(cr, uid, product,
                                         context=context_partner)
            if product.reserves_count:
                result['value']['qty_reserved'] = product.reserves_count
            else:
                result['value']['qty_reserved'] = 0.0
        return result
