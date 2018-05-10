# -*- coding: utf-8 -*-
# © 2018 Visiotech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields, _
from datetime import datetime, timedelta
from decimal import Decimal
import pandas
from pandas.tseries.offsets import BDay


class SaleReport(models.TransientModel):
    _name = 'xls.sale.report.wizard'

    @api.multi
    def _calc_data(self, calc_data, thirty_days_sales):
        """
        Calculate data depending of the 30D sales
        :param calc_data:
        :param thirty_days_sales:
        :return Decimal:
        """
        for sale_report in self:
            res = ''
            paydays = Decimal((((calc_data * 100) / thirty_days_sales) * 30) / 100)
            if paydays != 0.0:
                res = paydays
            return res

    @api.multi
    def _get_autocartera(self):
        """
        Calculate data account_move_line with filter 'autocartera'
        :return Float:
        """
        for sale_report in self:
            move_line_obj = sale_report.env['account.move.line']
            payment_term_ids = self.env['account.payment.term'].search([('name', 'ilike', 'Pago inmediato')]).ids
            move_line_ids = move_line_obj.search_read([('account_id.type', '=', 'receivable'),
                                                      ('reconcile_id', '=', False),
                                                      ('payment_term_id', 'not in', payment_term_ids),
                                                      ('stored_invoice_id', '!=', False)], ['maturity_residual'])
            autocartera = 0.0
            for move_line in move_line_ids:
                autocartera += move_line['maturity_residual']
            return autocartera

    @api.multi
    def _get_inventory_value(self, date_search):
        """
        Calculate stock inventory value at date_search.
        :param date_search:
        :return Float:
        """
        for sale_report in self:
            #name = False
            #attr = False
            #ctx = dict(self._context)
            #ctx.update({
            #    'history_date': history_date
            #})
            stock_history_obj = sale_report.env['stock.history']
            #res = stock_history_obj._get_inventory_value(False, False, context=ctx)
            product_tmpl_obj = sale_report.env["product.template"]
            product_obj = sale_report.env["product.product"]
            res = 0.0
            location_ids = [self.env.ref('crm_rma_advance_location.stock_location_rma').id,
                            self.env.ref('location_moves.stock_location_damaged').id]
            for location in self.env['stock.location'].search([('name', '=', 'Averiados')]).ids:
                location_ids.append(location)
            stock_history_data = stock_history_obj.search_read([('date', '<=', date_search),
                                                                ('location_id', 'not in', location_ids)],
                                                                ['quantity', 'price_unit_on_quant', 'product_id', 'company_id'])

            for line in stock_history_data:
                if line['product_id']:
                    product_data = product_obj.search_read([('id', '=', line['product_id'][0])], ['product_tmpl_id', 'cost_method'])
                    if product_data:
                        product = product_data[0]
                        product_tmpl_data = product_tmpl_obj.search_read([('id', '=', product['product_tmpl_id'][0])], ['id'])
                        if product_tmpl_data:
                            product_tmpl = product_tmpl_data[0]
                            if product['cost_method'] == 'real':
                                res += float(line['quantity'] * line['price_unit_on_quant'])
                            else:
                                res += float(line['quantity'] *\
                                             product_tmpl_obj.get_history_price(product_tmpl['id'],
                                                                                line['company_id'][0], date=date_search,
                                                                                context=sale_report.env.context))

            return res

    @api.multi
    def _select(self):
        this_str = """ 
            SELECT date_confirm::date, sum(price_total) as daily_sales,
            sum(benefit) as daily_benefit """
        return this_str

    @api.multi
    def _select_margin_month(self):
        this_str = """ 
            SELECT sum(price_total) as monthly_sales,
            sum(benefit) as monthly_benefit """
        return this_str

    @api.multi
    def _select_thirty_days_sales(self):
        this_str = """ 
            SELECT sum(price_total) as thirty_days_sales"""
        return this_str

    @api.multi
    def _from(self):
        from_str = """ 
        FROM sale_report
        """
        return from_str

    @api.multi
    def _where(self, date_start, date_end):
        where_str = "WHERE state not in ('draft', 'cancel') " \
                    "and date_confirm <= '" + date_end + "'::TIMESTAMP " \
                    "and date_confirm >= '" + date_start + "'::TIMESTAMP " \
                    "and company_id = 1"
        return where_str

    @api.multi
    def _where_stock(self, date):
        where_str = "WHERE state not in ('draft', 'cancel') " \
                    "and date_confirm <= '" + date + "'::TIMESTAMP " \
                    "and company_id = 1"
        return where_str

    @api.multi
    def _group_by(self):
        group_by_str = """
            GROUP BY date_confirm::DATE 
            ORDER BY date_confirm::DATE asc
        """
        return group_by_str

    @api.multi
    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days) + 1):
            yield start_date + timedelta(n)

    @api.multi
    def sale_report_data(self):
        self.ensure_one()
        new_dict = {}
        datas = {
            'model': 'xls.sale.report.wizard',
            'ids': [self.id],
            'data': []
        }

        date_today = datetime.now().replace(day=17, month=4, year=2018, hour=8, minute=0, second=0)
        date_today = date_today.strftime('%m-%d-%Y %H:%M:%S')
        margin_monthly_sql = self._select_margin_month() + self._from() + self._where_stock(date_today)
        self.env.cr.execute(margin_monthly_sql)
        margin_monthly_sql_data = self.env.cr.fetchall()

        date_yesterday_start = datetime.now().replace(day=17, month=4, year=2018, hour=0, minute=0, second=0) - BDay(1)
        date_yesterday_end = date_yesterday_start.replace(hour=23, minute=59, second=59)
        date_yesterday_start = date_yesterday_start.strftime('%m-%d-%Y %H:%M:%S')
        date_yesterday_end = date_yesterday_end.strftime('%m-%d-%Y %H:%M:%S')
        sql = self._select() + self._from() + self._where(date_yesterday_start, date_yesterday_end) + self._group_by()
        self.env.cr.execute(sql)
        sql_data = self.env.cr.fetchall()

        init_date = datetime.now().replace(day=17, month=4, year=2018, hour=8, minute=0, second=0) - BDay(31)
        init_date = init_date.replace(hour=0, minute=0, second=0)
        init_date = init_date.strftime('%m-%d-%Y %H:%M:%S')
        finish_date = datetime.now().replace(hour=23, minute=59, second=59) - BDay(1)
        finish_date = finish_date.strftime('%m-%d-%Y %H:%M:%S')
        thirty_days_sql = self._select_thirty_days_sales() + self._from() + self._where(init_date, finish_date)
        self.env.cr.execute(thirty_days_sql)
        thirty_days_sql_data = self.env.cr.fetchall()

        if sql_data:
            if sql_data[0][1] == 0:
                daily_margin = -100.00
            else:
                daily_margin = (sql_data[0][2] * 100) / sql_data[0][1]
            autocartera = Decimal(self._get_autocartera())
            inventory_value = Decimal(self._get_inventory_value(date_today))
            new_dict = {
                    'date': sql_data[0][0],
                    'daily_sales': Decimal(sql_data[0][1]),
                    'daily_benefit': Decimal(sql_data[0][2]),
                    'daily_margin': Decimal(daily_margin),
                    'inventory_value': inventory_value,
                    'autocartera': autocartera
            }
            monthly_margin = 0.0
            if margin_monthly_sql_data:
                if margin_monthly_sql_data[0][0] == 0:
                    monthly_margin = -100
                else:
                    monthly_margin = (margin_monthly_sql_data[0][1] * 100) / margin_monthly_sql_data[0][0]
            thirty_days_sales = Decimal(thirty_days_sql_data[0][0])
            new_dict.update(
                {
                    'monthly_margin': Decimal(monthly_margin),
                    'thirty_days_sales': thirty_days_sales,
                    'paydays': self._calc_data(autocartera, thirty_days_sales),
                    'thirty_days_stock': self._calc_data(inventory_value, thirty_days_sales)
                }
            )

            datas['data'].append(new_dict)
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'xls.daily.sale',
            'datas': datas
        }
