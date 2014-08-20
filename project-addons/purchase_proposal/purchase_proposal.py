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

from openerp import models, fields, api
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class purchase_proposal(models.Model):

    _name = "purchase.proposal"

    product_id = fields.Many2one('product.product', 'product')
    date = fields.Date('Date', default=fields.Date.context_today)
    qty = fields.Float('Quantity')
    supplier_id = fields.Many2one('res.partner', 'Supplier')
    state = fields.Selection((('new', 'New'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')), 'State', default='new')

    @api.one
    def act_done(self):
        self.state = 'done'


    @api.one
    def act_cancel(self):
        self.state = 'cancel'


    def get_quantity(self, product):
        '''"""
            Manufacturing: days from PO confirming to shipping.
            Transport: days from shipping confirmation to warehouse arrival.
            Purchasing cycle: average days between 2 purchasing orders.
            Security Margin: days of stock to keep just in case…
            Stock days: (stock * 60) / (quantity sold in last 60 days + reserved quantity)
            Daily consumption: (quantity sold in last 60 days + reserved quantity)/60
        """
            if today + STOCKY DAYS > FIRST ARRIVAL: #not stock breaking
                if  (MANUFACTURING + TRANSPORT + MARGIN)*DAYLY QTY> STOCK + ARRIVAL QTY: # ordering today, arrives on time
                    if (MANUFACTURING + TRANSPORT +MARGIN)*DAYLY QTY– (STOCK + ARRIVAL QTY) > MARGIN QTY: #difference is bigger than one month worth of stock
                        ORDER QUANTITY = DAILY QTY*(CYCLE+MARGIN)
                    else:
                        ORDER QUANTITY = DAILY QTY*(CYCLE+MARGIN) + STOCK+ARRIVAL QTY – (MANUFACTURING+TRANSPORT+MARGIN)*DAYLY QTY
                else:#ordering today, cannot arrive on time
                    ORDER QUANTITY = DAILY QTY* (CYCLE + MANUFACTURING + TRANSPORT + MARGIN)-STOCK-ARRIVAL QUANTITY
            else:#stock breaking
                if (NEXT ORDER DATE-ARRIVAL DATE+MANUFACTURING+TRANSPORT+MARGIN)*DAYLY QTY> ARRIVAL QTY:
                    if (NEXT ORDER DATE-ARRIVAL DATE+MANUFACTURING+TRANSPORT+MARGIN)*DAYLY QTY – ARRIVAL QTY >  MARGIN QTY:
                        ORDER QUANTITY=DAYLY QTY*(CYCLE + MARGIN)
                    else:
                        ORDER QUANTITY=DAYLY QTY*(CYCLE + MARGIN) + ARRIVAL QTY – DAILY QTY * (NEXT ORDER DATE – ARRIVAL DATE                                                                       +MANUFACTURING+TRANSPORT+MARGIN)
                else:
                    ORDER QUANTITY=DAYLY QTY*(CYCLE+NEXT ORDER DATE-ARRIVAL DATE+MANUFACTURING+TRANSPORT+MARGIN)-ARRIVAL QTY
        '''

        manufacturing = 0
        transport = 0
        purchasing_cycle = 0
        security_margin = product.security_margin

        #calculo de stock_days (stock * 60) / (quantity sold in last 60 days + reserved quantity)
        two_months_ago = date.today() + relativedelta(days=-60)
        total_qty = self.env['sale.order.line'].read_group(
            [('product_id', '=', product.id), ('order_id.date_order', '>=', two_months_ago.strftime('%Y-%m-%d'))], ['product_uom_qty', 'product_id'], ['product_id'])
        total_qty_last_months = total_qty and total_qty[0] and total_qty[0].get('product_uom_qty', False)
        stock_days = (product.qty_available * 60) / (total_qty_last_months + product.reserves_count)

        #Daily consumption: (quantity sold in last 60 days + reserved quantity)/60

        daily_consumption = (total_qty_last_months + product.reserves_count) / 60

        last_move = self.env['stock.move'].search(
            [('product_id', '=', product.id),
             ('picking_id.picking_type_code', '=', 'incoming'),
             ('picking_id.state', 'not in', ('draft', 'cancel', 'done'))],
            limit=1, order='date_expected')
        last_move_date = datetime.strptime(last_move, '%Y-%m-%d %H:%M:%S').date()

        if date.today() + relativedelta(days=stock_days) > last_move_date:
            pass

    @api.model
    def run_scheduler(self, automatic=False, use_new_cursor=False):
        products = self.env['product.product'].search([('sale_ok', '=', True)])

        for product in products:
            qty  = self.get_quantity(product)

