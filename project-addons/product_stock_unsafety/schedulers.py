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
from openerp.osv import osv
from openerp.tools.translate import _
import openerp
from openerp import api


class procurement_order(osv.Model):
    _inherit = 'procurement.order'

    @api.multi
    def update_under_minimum(self, vals):
        """
        First check if already exists under_minimum in purchase state. If
        exists we do nothing. If not exist we check if exist under_minimum
        in progress state, if that case we update it else we create a new one
        """

        stock_unsafety = self.env['product.stock.unsafety']
        domain = [
            ('state', '=', 'in_action'),
            ('product_id', '=', vals['product_id'])
        ]
        under_mins = stock_unsafety.search(domain)
        if not under_mins:
            domain = [
                ('state', 'in', ['in_progress', 'exception']),
                ('product_id', '=', vals['product_id'])
            ]
            under_mins = stock_unsafety.search(domain)
            if under_mins:
                under_mins.write(vals)
            else:
                stock_unsafety.create(vals)
        return

    def _procure_orderpoint_confirm(self, cr, uid, use_new_cursor=False,
                                    company_id=False, context=None):
        '''
        Create procurement based on Orderpoint
        :param bool use_new_cursor: if set, use a dedicated cursor and
            auto-commit after processing each procurement.
            This is appropriate for batch jobs only.
         If the remaining days of product sales are less than the
         minimum selling days configured in the rule of minimum stock
         of the product. So instead of creating another provision that would
         create a purchase, ast would by default,
         creates a under minimum model.
        '''
        if context is None:
            context = {}
        if use_new_cursor:
            cr = openerp.registry(cr.dbname).cursor()
        orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')
        pull_obj = self.pool.get('procurement.rule')
        bom_obj = self.pool.get('mrp.bom')

        dom = company_id and [('company_id', '=', company_id)] or []
        orderpoint_ids = orderpoint_obj.search(cr, uid, dom)
        prev_ids = []
        while orderpoint_ids:
            ids = orderpoint_ids[:100]
            del orderpoint_ids[:100]
            for op in orderpoint_obj.browse(cr, uid, ids, context=context):
                prod = op.product_id
                if not prod.active or prod.replacement_id:
                    continue
                domain = ['|', ('warehouse_id', '=', op.warehouse_id.id),
                          ('warehouse_id', '=', False),
                          ('location_id', '=', op.location_id.id)]
                product_route_ids = \
                    [x.id for x in
                     prod.route_ids + prod.categ_id.total_route_ids]
                rule_ids = pull_obj.search(cr, uid,
                                           domain + [('route_id', 'in',
                                                      product_route_ids)],
                                           order='route_sequence, sequence',
                                           context=context)
                if rule_ids:
                    seller = False
                    bom_id = False
                    delay = 0
                    rule = pull_obj.browse(cr, uid, rule_ids[0],
                                           context=context)
                    if rule.action == 'manufacture':
                        product_type = 'manufacture'
                        bom_id = bom_obj._bom_find(cr, uid, product_id=prod.id,
                                                   properties=[],
                                                   context=context)
                        if not bom_id:
                            state = 'exception'
                        else:
                            state = 'in_progress'
                            delay = prod.produce_delay or 0
                            bom_id = bom_id
                    else:
                        product_type = 'buy'
                        if prod.seller_ids:
                            seller = prod.seller_ids[0]
                            state = 'in_progress'
                            delay = seller.delay or 0
                        else:
                            state = 'exception'
                else:
                    state = 'exception'

                days_sale = prod.remaining_days_sale
                min_days_sale = op.min_days_id.days_sale
                real_minimum = min_days_sale + delay
                if (days_sale < real_minimum):
                    vals = {'product_id': prod.id,
                            'name': _('Minimum Stock Days'),
                            'supplier_id': seller and seller.name.id or False,
                            'orderpoint_id': op.id,
                            'responsible': uid,
                            'state': state,
                            'min_days_id': op.min_days_id.id,
                            'bom_id': bom_id,
                            'product_type': product_type,
                            'brand_id': prod.product_brand_id.id}
                    daylysales = prod.get_daily_sales()
                    remaining_days = real_minimum - days_sale
                    if daylysales and remaining_days:
                        vals['minimum_proposal'] = \
                            round(daylysales * remaining_days)

                    # Creating or updating existing under minimum
                    self.update_under_minimum(cr, uid, ids, vals,
                                              context=context)

            if use_new_cursor:
                cr.commit()
            if prev_ids == ids:
                break
            else:
                prev_ids = ids

        if use_new_cursor:
            cr.commit()
            cr.close()
        return {}
