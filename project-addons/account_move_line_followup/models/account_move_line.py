# -*- coding: utf-8 -*-

from openerp import models, api


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

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

