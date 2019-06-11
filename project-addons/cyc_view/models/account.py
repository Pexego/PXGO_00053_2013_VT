# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    cyc_notify_date = fields.Date("C&C notify date")
    cyc_limit_date_insolvency = fields.Date("C&C limit date insolvency")

    @api.model
    def create(self, vals):
        # Check if it is a positive account move line with customer invoice origin
        if vals.get('account_id', False) == 443 and vals.get('debit', False) > 0:
            invoice = self.env.context.get('invoice', False)
            if invoice and invoice.type == 'out_invoice' and vals.get('date_maturity', False):
                date_maturity = vals['date_maturity']
                cyc_days = self.env['ir.config_parameter'].get_param('notification.period.days.cyc')
                if not isinstance(date_maturity, datetime):
                    date_maturity = datetime.strptime(date_maturity, "%Y-%m-%d")
                limit_date = date_maturity + relativedelta(days=int(cyc_days))
                limit_date_format = limit_date.strftime("%Y-%m-%d")
                # Update cyc limit date with a predefined margin of days
                vals.update({'cyc_limit_date_insolvency': limit_date_format})
        res = super(AccountMoveLine, self).create(vals)
        return res

    # De momento no contemplar el caso de que se cambie la fecha de vencimiento desde el efecto
    '''@api.multi
    def write(self, vals, context=None, check=True, update_check=True):
        if vals.get('date_maturity') and self.account_id.id == 443 and self.debit > 0\
                and self.invoice and self.invoice.type == 'out_invoice':
            cyc_days = self.env['ir.config_parameter'].get_param('notification.period.days.cyc')
            limit_date = datetime.strptime(vals['date_maturity'], "%Y-%m-%d") + relativedelta(days=int(cyc_days))
            limit_date_format = limit_date.strftime("%Y-%m-%d")
            vals.update({'cyc_limit_date_insolvency': limit_date_format})
        res = super(AccountMoveLine, self).write(vals, context=context, check=check, update_check=update_check)
        return res'''
