from odoo import api, fields, models
from odoo.addons.base.ir.ir_cron import _intervalTypes
from datetime import datetime
from croniter import croniter
from dateutil.relativedelta import relativedelta


def get_delta_crontab_end_month():
    iter = croniter('45 23 L * *', datetime.now())
    # The actual next call must be today for this to work
    difference = iter.get_next(datetime) - datetime.now()
    return relativedelta(days=difference.days)


_intervalTypes['end_month'] = lambda interval: get_delta_crontab_end_month()


class ir_cron(models.Model):

    _inherit = "ir.cron"

    interval_type = fields.Selection(selection_add=[('end_month', 'End of month')])
