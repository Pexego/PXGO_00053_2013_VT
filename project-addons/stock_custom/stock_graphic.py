# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos S.L.
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
from openerp.osv import fields, orm
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning

import StringIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import base64
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd


class ProductTemplate(orm.Model):

    _inherit = 'product.template'

    _columns = {
        'date_start': fields.date("Start date"),
        'date_end': fields.date("End Date"),
        'period': fields.selection([('week', 'Week'),
                                    ('month', 'Month'),
                                    ('year', 'Year')
                                    ], 'Time Period'),
        'analysis_type': fields.selection([('average', 'Average'),
                                           ('end_of_period', 'End of period')
                                           ], 'Type of analysis'),
        'stock_graphic': fields.binary("Graph")
    }

class ProductProduct(orm.Model):

    _inherit = 'product.product'

    @api.model
    def _last_day_of_period(self, _date):
        if self.period == 'week':
            period_end = (datetime(_date.year, _date.month, _date.day) + relativedelta(weeks=1))
        elif self.period == 'year':
            period_end = (datetime(_date.year, _date.month, _date.day) + relativedelta(years=1))
        else:
            period_end = (datetime(_date.year, _date.month, _date.day) + relativedelta(months=1))
        return period_end + relativedelta(days=-1)

    @api.multi
    def _get_periods(self):
        """
        :return: A list of tuples with the first and last date
        """
        periods = []
        end_date = datetime.strptime(self.date_end, "%Y-%m-%d")  # datetime(today.year, today.month, 1)
        start_date = datetime.strptime(self.date_start, "%Y-%m-%d")  # datetime(today.year-1, today.month, 1)

        date_aux = start_date
        while date_aux < end_date:
            end_period = self._last_day_of_period(date_aux)
            period = (date_aux, end_period)
            periods.append(period)
            date_aux = end_period + relativedelta(days=1)

        return periods

    @api.multi
    def _get_stock_data(self):
        """
        :return: A list of tuples with the total of stock grouped
        """
        data = []
        stock_inventory = self.env['stock.inventory.line']

        # LOCATIONS = REAL + EXTERNAL STOCK
        locations = [self.env.ref("stock.stock_location_stock").id,
                     self.env.ref("location_moves.stock_location_external").id]

        for period in self._get_periods():
            start_period = period[0].strftime('%Y-%m-%d')
            end_period_aux = period[1]
            end_period = end_period_aux.strftime('%Y-%m-%d')
            end_period_seconds = time.mktime(end_period_aux.timetuple())
            total_stock = 0
            if self.analysis_type == 'average':
                for loc in locations:
                    stock_data = stock_inventory.read_group(
                        [('product_id', '=', self.id),
                         ('create_date', '>=', start_period),
                         ('create_date', '<=', end_period),
                         ('location_id', '=', loc)],
                        ['inventory_id', 'product_qty'],
                        ['inventory_id'])
                    total = 0
                    if stock_data:
                        for product_stock in stock_data:
                            total += product_stock['product_qty']
                        total /= len(stock_data)
                    total_stock += total

                if total_stock:
                    data.append([end_period_seconds, total_stock])

            else:
                for loc in locations:
                    stock_data = stock_inventory.read_group(
                        [('product_id', '=', self.id),
                         ('create_date', '>=', start_period),
                         ('create_date', '<=', end_period),
                         ('location_id', '=', loc)],
                        ['inventory_id', 'product_qty'],
                        ['inventory_id'], limit=1, orderby='inventory_id DESC')
                    if stock_data:
                        total_stock += stock_data[0]['product_qty']

                if total_stock:
                    data.append([end_period_seconds, total_stock])

        return data

    @api.multi
    def action_create_graph(self):

        if not self.date_start \
                or not self.date_end \
                or not self.period \
                or not self.analysis_type:
            raise except_orm(_('Error'), _(
                'You must set all filter values'))
        elif self.date_end < self.date_start:
            raise except_orm(_('Error'), _(
                'End date cannot be smaller than start date'))

        self.run_scheduler_graphic()

    @api.multi
    def run_scheduler_graphic(self):
        """
            Generate the graphs of stock and link it to the partner
        """
        period_filter = self.period
        if period_filter == 'week':
            format_xlabel = "%y-W%W"
        elif period_filter == 'year':
            format_xlabel = "%Y"
        else:
            format_xlabel = "%m-%y"
        int_to_date = lambda x: \
            datetime(time.localtime(x).tm_year, time.localtime(x).tm_mon,
                     time.localtime(x).tm_mday).strftime(format_xlabel)

        data = self._get_stock_data()
        if data:
            # Get data
            df = pd.DataFrame()
            df['Date'] = range(len(data))
            df['Stock'] = [x[1] for x in data]

            min_stock = min(df['Stock'])
            max_stock = max(df['Stock'])

            if min_stock != max_stock:
                margin_y = (max_stock - min_stock) / 15
                margin_x = (len(data)) / 40.0
                offset_axis = (max_stock - min_stock) / 10
            else:
                margin_y = max_stock / 100
                margin_x = 0
                offset_axis = max_stock / 10

            # Create plot with points
            sns.despine()
            sns.set_style("darkgrid", {"axes.labelcolor": "#363737",
                                       "ytick.color": "#59656d", "xtick.color": "#59656d"})
            sns_plot = sns.lmplot('Date', 'Stock', data=df, fit_reg=False, size=5, aspect=1.7,
                                  scatter_kws={"color": "#A61D34", "s": 30})

            # Draw a line plot to join all points
            sns_plot.map(plt.plot, "Date", "Stock", marker="o", ms=4, color='#A61D34')
            plt.xticks(range(len(data)), [int_to_date(x[0]) for x in data])
            [sns_plot.ax.text(p[0] - margin_x, p[1] + margin_y, '%d' % int(p[1]), color='grey', fontsize=9)
             for p in zip(sns_plot.ax.get_xticks(), df['Stock'])]

            # Set axis config
            plt.ylim(min_stock - offset_axis, max_stock + offset_axis)
            sns_plot.set_xticklabels(rotation=30)

            # Create the graphic with the data
            io = StringIO.StringIO()
            sns_plot.savefig(io, format='png')
            io.seek(0)
            img_data = base64.b64encode(io.getvalue())
            plt.close()
            self.write({'stock_graphic': img_data})

        return
