# -*- coding: utf-8 -*-

from openerp import models, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    @api.model
    def create(self, vals):
        # Check if it is a positive account move line with customer invoice origin
        if vals.get('account_id', False) == 443 and vals.get('debit', False) > 0:
            invoice = self.env.context.get('invoice', False)
            if invoice and invoice.type == 'out_invoice' and vals.get('date_maturity', False):
                date_maturity = vals['date_maturity']
                cyc_days = self.env['ir.config_parameter'].get_param('notification.period.days.cyc')
                limit_date = datetime.strptime(date_maturity, "%Y-%m-%d") + relativedelta(days=int(cyc_days))
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

    @api.model
    def cron_update_date_followup(self):
        # Searching refund account move line
        refund_aml = self.search([('reconcile_id', '=', False), ('account_id', '=', 443),
                                  ('credit', '!=', 0), ('invoice.type', '=', 'out_refund')])

        for aml in refund_aml:
            # Searching the most unfavorable maturity date on positive payments
            aml_partner = self.search_read([('partner_id', '=', aml.partner_id.id),
                                            ('reconcile_id', '=', False),
                                            ('account_id', '=', 443),
                                            ('debit', '!=', 0)],
                                           ['date_maturity', 'followup_line_id', 'followup_date'],
                                           limit=1, order="date_maturity asc")
            # Updating maturity date and follow-up data
            if aml_partner:
                aml_partner_data = aml_partner[0]
                aml.write({'date_maturity': aml_partner_data['date_maturity'],
                           'followup_line_id': aml_partner_data['followup_line_id'] and
                                               aml_partner_data['followup_line_id'][0] or False,
                           'followup_date': aml_partner_data['followup_date']})

