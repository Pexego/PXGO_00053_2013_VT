# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp import models, fields, tools


class sale_order_line_report(models.Model):

    _name = 'sale.order.line.report'
    _auto = False

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', 'Partner')
    product_qty = fields.Float('Quantity')
    uom = fields.Many2one('product.uom', 'UoM')
    price_unit =  fields.Float('Price unit')
    discount = fields.Float('Discount')
    salesman_id = fields.Many2one('res.users', 'Salesperson')
    state = fields.Char('State')
    product_id = fields.Many2one('product.product', 'Product')
    order_id = fields.Many2one('sale.order', 'Order')
    qty_kitchen = fields.Float('Qty in kitchen', group_operator="avg")
    qty_stock = fields.Float('Stock qty', group_operator="avg")

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""
CREATE or REPLACE VIEW sale_order_line_report as (SELECT sol.id as id,
       sol.name as name,
       sol.order_partner_id as partner_id,
       sol.product_uom_qty as product_qty,
       sol.product_uom as uom,
       sol.price_unit as price_unit,
       sol.discount as discount,
       sol.salesman_id as salesman_id,
       sol.state as state,
       sol.order_id as order_id,
       q_kt.product_id,
       q_kt.qty AS qty_kitchen,
       stck.qty AS qty_stock
FROM   sale_order_line sol
       LEFT JOIN (SELECT product_id,
                          Sum(qty) AS qty
                   FROM   stock_quant
                   WHERE  location_id IN (SELECT res_id
                                          FROM   ir_model_data
                                          WHERE  module = 'location_moves' AND name IN ('stock_location_kitchen','stock_location_pantry')
                                                 )
                   GROUP  BY product_id) q_kt
               ON sol.product_id = q_kt.product_id
       LEFT JOIN (SELECT product_id,
                          Sum(qty) AS qty
                   FROM   stock_quant
                   WHERE  location_id IN (SELECT loc.id
                                          FROM   stock_location loc
                          INNER JOIN (SELECT parent_left,
                                             parent_right
                                      FROM   stock_location
                                      WHERE
                          id IN (select view_location_id from stock_warehouse))
                                     stock
                                  ON loc.parent_left >=
                                     stock.parent_left
                                     AND loc.parent_right <=
                                         stock.parent_right)
                   GROUP  BY product_id) stck
               ON sol.product_id = stck.product_id
WHERE  q_kt.qty > 0 and sol.id in (select sale_line_id from procurement_order po where po.state not in ('done', 'cancel'))
GROUP BY sol.id, sol.name, sol.order_partner_id, sol.product_uom_qty,
         sol.product_uom, sol.price_unit, sol.discount,
         sol.salesman_id, sol.state, sol.order_id, q_kt.product_id, q_kt.qty, stck.qty)
""")
