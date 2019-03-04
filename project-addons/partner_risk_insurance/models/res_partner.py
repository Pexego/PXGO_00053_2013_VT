
# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.depends('company_credit_limit', 'insurance_credit_limit')
    def _credit_limit(self):
        for partner in self:
            partner.credit_limit = (partner.company_credit_limit +
                                    partner.insurance_credit_limit)

    def _is_accounting(self):
        accountant = self.env.ref('account.group_account_manager')
        is_accountant = self.env.user.id in accountant.users.ids
        for partner in self:
            if is_accountant:
                partner.is_accounting = True
            else:
                partner.is_accounting = False

    credit_limit = fields.Float('Credit Limit', store=True,
                                compute=_credit_limit)
    company_credit_limit = fields.Float("Company's Credit Limit",
                                        help='Credit limit granted by the '
                                        'company.')
    insurance_credit_limit = fields.Float("Insurance's Credit Limit",
                                          help='Credit limit granted by the '
                                          'insurance company.')
    risk_insurance_coverage_percent = fields.Float(
        "Insurance's Credit Coverage", help='Percentage of the credit covered '
        'by the insurance.')
    risk_insurance_requested = fields.Boolean(
        'Insurance Requested', help='Mark this field if an insurance was '
        'requested for the credit of this partner.')
    risk_insurance_grant_date = fields.Date('Insurance Grant Date',
                                            help='Date when the insurance was '
                                            'granted by the insurance company.'
                                            )
    risk_insurance_code = fields.Char('Insurance Code',
                                      help='Code assigned to this partner by '
                                      'the risk insurance company.')
    risk_insurance_code_2 = fields.Char('Insurance Code 2',
                                        help='Secondary code assigned to this '
                                        'partner by the risk insurance '
                                        'company.')

    risk_insurance_comment = fields.Text('Comments')

    is_accounting = fields.Boolean('Is Acounting', compute="_is_accounting")
