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

    def _product_margin(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                'margin': 0.0,
                'margin_perc': 0.0,
            }

            margin = 0.0
            if line.product_id:
                if line.purchase_price:
                    margin = round((line.price_unit * line.product_uos_qty *
                                   (100.0 - line.discount) / 100.0) -
                                   (line.purchase_price *
                                    line.product_uos_qty), 2)
                    res[line.id]['margin_perc'] = round((margin * 100) /
                                                        (line.purchase_price *
                                                         line.product_uos_qty),
                                                        2)
                elif line.product_id.standard_price:
                    margin = round((line.price_unit * line.product_uos_qty *
                                    (100.0 - line.discount) / 100.0) -
                                   (line.product_id.standard_price *
                                    line.product_uos_qty), 2)
                    res[line.id]['margin_perc'] = round((margin * 100) /
                                                        (line.product_id.standard_price *
                                                         line.product_uos_qty),
                                                        2)
                res[line.id]['margin'] = margin
        return res

    _columns = {
        'margin': fields.function(_product_margin, string='Margin',
                                  store=True, multi='marg'),
        'margin_perc': fields.function(_product_margin, string='Margin',
                                       store=True, multi='marg'),
    }


class sale_order(orm.Model):

    _inherit = "sale.order"

    def _product_margin(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for sale in self.browse(cr, uid, ids, context=context):
            total_purchase = sale.total_purchase or \
                self._get_total_price_purchase(cr, uid, ids, 'total_purchase',
                                               arg, context)[sale.id]

            result[sale.id] = 0.0
            if total_purchase != 0:
                for line in sale.order_line:
                    if not line.deposit:
                        result[sale.id] += line.margin or 0.0
                result[sale.id] = round((result[sale.id] * 100) /
                                        total_purchase, 2)
        return result

    def _get_total_price_purchase(self, cr, uid, ids, field_name, arg,
                                  context=None):
        result = {}
        for sale in self.browse(cr, uid, ids, context=context):
            result[sale.id] = 0.0
            for line in sale.order_line:
                #ADDED for dependency with stock_deposit for not count deposit in total margin
                if not line.deposit:
                    if line.product_id:
                        if line.purchase_price:
                            result[sale.id] += line.purchase_price * \
                                line.product_uos_qty
                        else:
                            result[sale.id] += line.product_id.standard_price * \
                                line.product_uos_qty
        return result

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        sale_obj = self.pool.get('sale.order.line')
        for line in sale_obj.browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'total_purchase': fields.function(_get_total_price_purchase,
                                          string='Price purchase',
                                          store={
                                              'sale.order.line': (_get_order,
                                                                  ['margin', 'deposit'],
                                                                  20),
                                              'sale.order': (lambda self, cr,
                                                             uid, ids, c={}:
                                                             ids,
                                                             ['order_line'],
                                                             20),
                                          }),
        'margin': fields.function(_product_margin, string='Margin',
                                  help="It gives profitability by calculating \
                                        percentage.",
                                  store={
                                      'sale.order.line':
                                          (_get_order, ['margin', 'deposit'], 20),
                                      'sale.order':
                                          (lambda self, cr, uid, ids, c={}:
                                           ids, ['order_line'], 20),
                                  }),
    }
