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
from openerp.tools.translate import _

import StringIO
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import base64
from pychart import *


class res_partner(orm.Model):

    _inherit = 'res.partner'

    _columns = {
        'sale_graphic': fields.binary("Sale graphic"),
    }

    def _last_day_of_month(self, _date):
        return (datetime(_date.year, _date.month, 1) + relativedelta(months=1)) + \
            relativedelta(days=-1)

    def _get_year_periods(self):
        """
        :return: A list of tuples with the first and last date of the month for
                 the last year
        """
        periods = []

        today = datetime.now()
        end_year = datetime(today.year, today.month, 1)
        start_year = datetime(today.year-1, today.month, 1)

        date_aux = start_year
        while date_aux < end_year:
            period = (date_aux, self._last_day_of_month(date_aux))
            periods.append(period)
            date_aux = date_aux + relativedelta(months=1)
        return periods

    def _get_partner_data(self, cr, uid, partner_id, context={}):
        """
        :return: A list of tuples with the total of sales grouped by the month
        """
        data = []
        sale_obj = self.pool.get('sale.order')
        for month_period in self._get_year_periods():
            start_month = month_period[0].strftime('%Y-%m-%d')
            end_month = month_period[1]
            end_month_str = end_month.strftime('%Y-%m-%d')
            end_month_seconds = time.mktime(end_month.timetuple())
            total_sale = sale_obj.read_group(cr, uid,
                                             [('partner_id', '=', partner_id),
                                              ('state', 'in', ['done']),
                                              ('date_order', '>=', start_month),
                                              ('date_order', '<=', end_month_str)],
                                             ['amount_total'],
                                             ['amount_total'],
                                             context=context)
            if total_sale:
                data.append([end_month_seconds, total_sale[0]['amount_total']])
        return data

    def run_scheduler_grpahic(self, cr, uid, automatic=False,
                              use_new_cursor=False, context=None):
        """
            Generate the graphs of sales and link it to the partner
        """
        partner_obj = self.pool.get('res.partner')
        if context is None:
            context = {}
        int_to_date = lambda x: '/a60{}' + \
            datetime(time.localtime(x).tm_year, time.localtime(x).tm_mon,
                     time.localtime(x).tm_mday).strftime('%m-%y')
        partner_ids = partner_obj.search(cr, uid, [('customer', '=', True)],
                                         context=context)
        for partner_id in partner_ids:
            data = self._get_partner_data(cr, uid, partner_id, context)
            if data:

                # Create the graphic with the data
                io = StringIO.StringIO()
                canv = canvas.init(fname=io, format='png')
                max_total = data[0][1]
                min_total = data[0][1]
                for tup in data[1:]:
                    if tup[1] > max_total:
                        max_total = tup[1]
                    elif tup[1] < min_total:
                        min_total = tup[1]
                min_total = min_total / 2
                ar = area.T(x_coord=category_coord.T(data, 0),
                            x_axis=axis.X(label=_("Date"), format=int_to_date),
                            y_axis=axis.Y(label=_("Amount total")),
                            x_range=(data[0][0], data[-1][0]),
                            y_range=(min_total, max_total),
                            legend=None,
                            size=(680, 450))

                ar.add_plot(bar_plot.T(data=data, fill_style=fill_style.red))

                ar.draw(canv)
                canv.close()
                img_data = base64.b64encode(io.getvalue())
                partner_obj.write(cr, uid, [partner_id],
                                  {'sale_graphic': img_data}, context)
        return
