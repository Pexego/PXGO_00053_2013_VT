# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
from openerp import models, fields, api


class ProductProduct(models.Model):

    _inherit = 'product.product'

    last_sixty_days_sales = fields.Float('Sales in last 60 days with stock',
                                         readonly=True)
    joking_index = fields.Float("Joking index", readonly=True)
    order_cycle = fields.Integer('Order cycle')
    transport_time = fields.Integer('Transport time')
    security_margin = fields.Integer('Security margin')
    average_margin = fields.Float("Average Margin Last Sales", readonly=True)

    @api.model
    def compute_last_sixty_days_sales(self):
        self.average_margin_last_sales()
        positive_days_obj = self.env['stock.days.positive']
        move_obj = self.env['stock.move']
        for product in self.search([('type', '!=', 'service')]):
            days = positive_days_obj.search([('product_id', '=', product.id)],
                                            limit=60, order='datum desc')
            if not days:
                product.last_sixty_days_sales = 0
                continue
            moves = move_obj.search([('date', '>=', days[-1].datum),
                                     ('state', '=', 'done'),
                                     ('product_id', '=', product.id),
                                     ('picking_type_id.code', '=',
                                      'outgoing')])
            product.last_sixty_days_sales = sum(
                [x.product_uom_qty for x in moves
                 if x.procurement_id.sale_line_id])
            product.joking_index = product.last_sixty_days_sales * \
                product.standard_price

    @api.model
    def average_margin_last_sales(self, ids = False):
        if not ids:
            sql_sentence = """
                SELECT DISTINCT product_id
                    FROM sale_order_line
                    WHERE state not in ('draft', 'cancel', 'exception')
                    AND product_id IS NOT NULL
            """
            self.env.cr.execute(sql_sentence)
            res = self.env.cr.fetchall()
            product_ids = [x[0] for x in res]
        else:
            product_ids = ids
        for product_id in self.browse(product_ids):
            sale_order_line_obj = self.env['sale.order.line']
            domain = [('product_id', '=', product_id.id)]
            sales_obj = sale_order_line_obj.search(domain, limit=100,
                                                   order='id desc')
            margin_perc_sum = 0
            qty_sum = 0
            for line in sales_obj:
                margin_perc_sum += (line.margin_perc * line.product_uom_qty)
                qty_sum += line.product_uom_qty
            if qty_sum:
                product_id.average_margin = margin_perc_sum / qty_sum
    @api.multi
    def average_margin_compute(self):
        self.average_margin_last_sales(ids=self.ids)
