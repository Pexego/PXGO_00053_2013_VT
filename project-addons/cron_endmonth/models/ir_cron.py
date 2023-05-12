from odoo import api, fields, models
from odoo.addons.base.ir.ir_cron import _intervalTypes
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar


def get_delta_end_month_w():
    next_month = (datetime.now() + relativedelta(months=1)).month
    next_year = datetime.now().year
    if next_month == 1:
        next_year += 1

    next_day = calendar.monthrange(next_year, next_month)[1]
    next_date = datetime(next_year, next_month, next_day)

    if next_date.weekday() in (5, 6):  # Saturday or Sunday
        # Having 5 (saturday) -4 will be 1 day less (friday) and 6-4 will be 2 days less
        days_to_decrease = next_date.weekday() - 4
        next_date = datetime.datetime(next_year, next_month, next_day - days_to_decrease)

    difference = next_date.date() - datetime.today().date()
    return relativedelta(days=difference.days)


def get_delta_end_month():
    next_month = (datetime.now() + relativedelta(months=1)).month
    next_year = datetime.now().year
    if next_month == 1:
        next_year += 1

    next_day = calendar.monthrange(next_year, next_month)[1]
    next_date = datetime(next_year, next_month, next_day)

    difference = next_date.date() - datetime.today().date()
    return relativedelta(days=difference.days)


_intervalTypes['end_month_w'] = lambda interval: get_delta_end_month_w()
_intervalTypes['end_month'] = lambda interval: get_delta_end_month()


class ir_cron(models.Model):

    _inherit = "ir.cron"

    interval_type = fields.Selection(selection_add=[('end_month_w', 'End of month Workday'), ('end_month', 'End of month')])
