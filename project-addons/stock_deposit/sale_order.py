# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Santi Argüeso
#    Copyright 2014 Pexego Sistemas Informáticos S.L.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from datetime import datetime, timedelta
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import SUPERUSER_ID, api
import openerp.addons.decimal_precision as dp


class sale_order_line(orm.Model):
    _inherit = 'sale.order.line'

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        values = super(sale_order_line, self)._amount_line(cr, uid,  ids, field_name, arg, context=context)
        for line in self.browse(cr, uid, ids, context=context):
            if line.deposit:
                values[line.id] = 0.0
        return values

    _columns = {
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
        'deposit': fields.boolean(
            'Deposit'),
        'deposit_date': fields.date('Date Dep.')
    }

    def onchange_deposit(self, cr, uid, ids, deposit, context=None):
        if deposit:
            current_date = datetime.utcnow()
            delta = timedelta(days=15)
            result = current_date + delta
            return {'value': {'deposit_date': result.strftime(DEFAULT_SERVER_DATE_FORMAT)}}
        else:
            return {'value': {'deposit_date': False}}

class sale_order(orm.Model):
    _inherit = 'sale.order'

    def _amount_line_tax(self, cr, uid, line, context=None):
        if line.deposit:
            return 0.0
        else:
            return super(sale_order, self)._amount_line_tax(cr, uid, line, context=context)


    def _prepare_order_line_procurement(self, cr, uid, order, line, group_id=False, context=None):
        vals = super(sale_order, self)._prepare_order_line_procurement(cr, uid, order, line, group_id=group_id, context=context)

        #FIX --  ONLY FOR TESTING
        # We have to obtain yhe location for deposit (TESTING)
        location_id = order.partner_shipping_id.property_stock_customer.id

        if line.deposit == True:
            mod_obj = self.pool.get('ir.model.data')
            deposit_id = mod_obj.get_object_reference(cr, uid, 'stock_deposit', 'stock_location_deposit')
            vals['location_id'] = deposit_id[1]
        return vals