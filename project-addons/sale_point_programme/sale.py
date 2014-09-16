# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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

from openerp import models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def action_button_confirm(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = super(SaleOrder, self).action_button_confirm(cr, uid, ids,
                                                           context=context)
        rule_obj = self.pool['sale.point.programme.rule']
        bag_obj = self.pool['res.partner.point.programme.bag']
        for order in self.browse(cr, uid, ids, context=context):
            total_product_qty = 0.0
            categories = {}
            products = {}
            rules = rule_obj.search(cr, uid, ['|', ('date_start', '<=',
                                                    order.date_order[:10]),
                                              ('date_start', '=', False),
                                              '|', ('date_end', '>=',
                                                    order.date_order[:10]),
                                              ('date_end', '=', False)],
                                    context=context)

            if rules:
                for line in order.order_line:
                    if line.product_id:
                        pkey = line.product_id.id
                        ckey = line.product_id.categ_id.id
                        if products.get(pkey):
                            products[pkey]['qty'] += line.product_uom_qty
                            products[pkey]['amount'] += line.price_subtotal
                        else:
                            products[pkey] = {'qty': line.product_uom_qty,
                                              'amount': line.price_subtotal}
                        if categories.get(ckey):
                            categories[ckey]['qty'] += line.product_uom_qty
                            categories[ckey]['amount'] += line.price_subtotal
                        else:
                            categories[ckey] = {'qty': line.product_uom_qty,
                                                'amount': line.price_subtotal}
                    total_product_qty += line.product_uom_qty

                for rule in rule_obj.browse(cr, uid, rules, context=context):
                    points = False
                    if rule.product_id:
                        if rule.product_id.id in products:
                            record = products[rule.product_id.id]
                            if rule.attribute == 'product_qty':
                                points = rule.evaluate(record['qty'])
                            else:
                                points = rule.evaluate(record['amount'])
                    elif rule.category_id:
                        if rule.category_id.id in categories:
                            record = categories[rule.category_id.id]
                            if rule.attribute == 'product_qty':
                                points = rule.evaluate(record['qty'])
                            else:
                                points = rule.evaluate(record['amount'])
                    elif rule.attribute == 'amount_untaxed':
                        points = rule.evaluate(order.amount_untaxed)
                    else:
                        points = rule.evaluate(total_product_qty)

                    if points and points[0]:
                        bag_obj.create(cr, uid,
                                       {'name': rule.name,
                                        'point_rule_id': rule.id,
                                        'order_id': order.id,
                                        'points': points[0],
                                        'partner_id': order.partner_id.id},
                                       context=context)
        return res

    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = super(SaleOrder, self).action_cancel(cr, uid, ids,
                                                   context=context)
        bag_obj = self.pool['res.partner.point.programme.bag']
        bag_ids = bag_obj.search(cr, uid, [('order_id', 'in', ids)],
                                 context=context)
        bag_obj.unlink(cr, uid, bag_ids, context=context)
        return res
