# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, _, api

from matplotlib import pyplot as plt
from io import BytesIO
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta
import time
import base64
import matplotlib
matplotlib.use('Agg')


class ResPartner(models.Model):

    _inherit = 'res.partner'

    sale_graphic = fields.Binary()

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

    def _get_partner_data(self):
        """
        :return: A list of tuples with the total of sales grouped by the month
        """
        self.ensure_one()
        data = []
        for month_period in self._get_year_periods():
            start_month = fields.Date.to_string(month_period[0])
            end_month_str = fields.Date.to_string(month_period[1])
            end_month_seconds = time.mktime(month_period[1].timetuple())
            total_sale = self.env['sale.order'].read_group(
                [('partner_id', 'child_of', self.id),
                 ('state', 'not in', ['draft', 'sent', 'cancel', 'reserve']),
                 ('date_order', '>=', start_month),
                 ('date_order', '<=', end_month_str)],
                ['amount_untaxed', 'partner_id'], ['partner_id'])
            if total_sale:
                total = 0.0
                for total_partner in total_sale:
                    total += total_partner['amount_untaxed']
                if total != 0:
                    data.append([end_month_seconds, total])
        return data

    def action_create_graph(self):
        self.ensure_one()
        self.with_context(partner_id=self.id).run_scheduler_grpahic()

    @api.model
    def run_scheduler_grpahic(self):
        """
            Generate the graphs of sales and link it to the partner
        """
        int_to_date = lambda x: \
            datetime(time.localtime(x).tm_year, time.localtime(x).tm_mon,
                     time.localtime(x).tm_mday).strftime('%m-%y')
        if self._context.get('partner_id', False):
            partners = self.browse(self._context['partner_id'])
        else:
            today = datetime.today()
            curr_month = today.month - 1
            curr_year = today.year
            if not curr_month:
                curr_month = 12
                curr_year -= 1
            last_day_in_month = calendar.monthrange(curr_year, curr_month)
            first_date = fields.Date.to_string(
                datetime(curr_year, curr_month, 1))
            last_date = fields.Date.to_string(
                datetime(curr_year, curr_month, last_day_in_month[1]))
            partner_ids = self.env['sale.order'].read_group(
                [('date_order', '>=', first_date),
                 ('date_order', '<=', last_date),
                 ('state', 'not in', ['draft', 'sent', 'cancel', 'reserve'])],
                ["partner_id"], groupby="partner_id")
            partners = self.browse([x["partner_id"][0] for x in partner_ids])
            partners = partners.mapped('commercial_partner_id')
        for partner in partners:
            data = partner._get_partner_data()
            if data:
                fig, ax = plt.subplots(figsize=(10, 6))
                x_pos = list(range(len(data)))
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
                io = BytesIO()
                fig.savefig(io, format='png')
                io.seek(0)
                img_data = base64.b64encode(io.getvalue())
                plt.close()
                partner.write({'sale_graphic': img_data})
        return
