# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Carlos Lombardía <carlos@comunitea.com>$
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
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, osv
from datetime import datetime

class purchase_order(osv.osv):

    _inherit = "purchase.order"

    def _minimum_planned_date(self, cr, uid, ids, field_name, arg, context=None):
        res={}
        purchase_obj=self.browse(cr, uid, ids, context=context)
        for purchase in purchase_obj:
            res[purchase.id] = False
            if purchase.order_line:
                min_date=purchase.order_line[0].date_planned
                for line in purchase.order_line:
                    if line.state == 'cancel':
                        continue
                    if line.date_planned < min_date:
                        min_date=line.date_planned
                res[purchase.id]=min_date
        return res

    def _set_minimum_planned_date(self, cr, uid, ids, name, value, arg, context=None):
        if not value: return False
        if type(ids)!=type([]):
            ids=[ids]
        pol_obj = self.pool.get('purchase.order.line')
        for po in self.browse(cr, uid, ids, context=context):
            if po.order_line:
                pol_ids = pol_obj.search(cr, uid, [
                    ('order_id', '=', po.id), '|', ('date_planned', '=', po.minimum_planned_date), ('date_planned', '<', value)
                ], context=context)
                pol_obj.write(cr, uid, pol_ids, {'date_planned': value}, context=context)
        self.invalidate_cache(cr, uid, context=context)
        return True

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _get_purchase_order(self, cr, uid, ids, context=None):
        result = {}
        for order in self.browse(cr, uid, ids, context=context):
            result[order.id] = True
        return result.keys()

    _columns = {
        'minimum_planned_date':fields.function(_minimum_planned_date, fnct_inv=_set_minimum_planned_date, string='Expected Date', type='datetime', select=True, help="This is computed as the minimum scheduled date of all purchase order lines' products.",
            store = {
                'purchase.order.line': (_get_order, ['date_planned'], 10),
                'purchase.order': (_get_purchase_order, ['order_line'], 10),
            }
        )
    }
