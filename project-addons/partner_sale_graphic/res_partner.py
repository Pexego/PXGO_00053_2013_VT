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
import calendar
from dateutil.relativedelta import relativedelta
import time
import base64
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt


class res_partner(orm.Model):

    _inherit = 'res.partner'

    _columns = {
        'sale_graphic': fields.binary("Sale graphic"),
    }

    def _last_day_of_month(self, _date):
        return (datetime(_date.year, _date.month, 1) +
                relativedelta(months=1)) + relativedelta(days=-1)

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
                                             [('partner_id', 'child_of',
                                               partner_id),
                                              ('state', 'not in',
                                               ['draft', 'sent', 'cancel',
                                                'reserve', 'waiting_date',
                                                'wait_risk', 'risk_approval']),
                                              ('date_order', '>=',
                                               start_month),
                                              ('date_order', '<=',
                                               end_month_str)],
                                             ['amount_untaxed', 'partner_id'],
                                             ['partner_id'],
                                             context=context)
            if total_sale:
                total = 0.0
                for total_partner in total_sale:
                    total += total_partner['amount_untaxed']
                if total != 0:
                    data.append([end_month_seconds, total])
        return data

    def action_create_graph(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context['partner_id'] = ids[0]
        self.run_scheduler_grpahic(cr, uid, context=context)

    def run_scheduler_grpahic(self, cr, uid, automatic=False,
                              use_new_cursor=False, context=None):
        """
            Generate the graphs of sales and link it to the partner
        """
        partner_obj = self.pool.get('res.partner')
        sale_obj = self.pool.get('sale.order')
        if context is None:
            context = {}
        int_to_date = lambda x: \
            datetime(time.localtime(x).tm_year, time.localtime(x).tm_mon,
                     time.localtime(x).tm_mday).strftime('%m-%y')
        if context.get('partner_id', False):
            partner_ids = [context['partner_id']]
        else:
            today = datetime.today()
            curr_month = today.month - 1
            curr_year = today.year
            if not curr_month:
                curr_month = 12
                curr_year -= 1
            last_day_in_month = calendar.monthrange(curr_year, curr_month)
            first_date = datetime(curr_year, curr_month, 1).\
                strftime("%Y-%m-%d")
            last_date = datetime(curr_year, curr_month,
                                 last_day_in_month[1]).strftime("%Y-%m-%d")
            partners = sale_obj.read_group(cr, uid,
                                           [('date_order', '>=', first_date),
                                            ('date_order', '<=', last_date),
                                            ('state', 'not in',
                                             ['draft', 'sent', 'cancel',
                                              'reserve', 'waiting_date',
                                              'wait_risk', 'risk_approval'])],
                                           ["partner_id"],
                                           groupby="partner_id")
            partner_ids = \
                [partner_obj.browse(cr, uid, x["partner_id"][0]).
                 commercial_partner_id.id
                 for x in partners]
            partner_ids = list(set(partner_ids))
            partner_len =  len(partner_ids)

        for partner_id in partner_ids:
            fig, ax = plt.subplots(figsize=(10, 6))
            data = self._get_partner_data(cr, uid, partner_id, context)
            if data:
                x_pos = range(len(data))
                rects1 = ax.bar(x_pos, [x[1] for x in data], 0.25, color='r')
                ax.set_ylabel(_("Amount total"))
                ax.set_xlabel(_("Date"))
                ax.margins(0.04)
                plt.xticks(x_pos, [int_to_date(x[0]) for x in data])
                for rect in rects1:
                    height = rect.get_height()
                    ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                            '%d' % int(height),
                            ha='center', va='bottom')

                fig = plt.gcf()

                # Create the graphic with the data
                io = StringIO.StringIO()
                fig.savefig(io, format='png')
                io.seek(0)
                img_data = base64.b64encode(io.getvalue())
                plt.close()
                partner_obj.write(cr, uid, [partner_id],
                                  {'sale_graphic': img_data}, context)
        return
