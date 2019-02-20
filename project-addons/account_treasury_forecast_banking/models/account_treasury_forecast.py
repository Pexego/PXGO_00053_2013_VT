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

import odoo.addons.decimal_precision as dp
from odoo import models, fields, api


class AccountTreasuryForecastInvoice(models.Model):
    _inherit = 'account.treasury.forecast.invoice'

    payment_mode_id = fields.Many2one('account.payment.mode', string="Payment Mode",
                                      store=True,
                                      related="invoice_id.payment_mode_id")
    invoice_type = fields.Selection([('out_invoice', 'Customer Invoice'),
                                     ('in_invoice', 'Supplier Invoice'),
                                     ('out_refund', 'Customer Refund'),
                                     ('in_refund', 'Supplier Refund')],
                                    string="Type", related='invoice_id.type')
    payment_term_id = fields.Many2one('account.payment.term',
                                      string="Payment Term",
                                      related='invoice_id.payment_term_id')


class AccountTreasuryForecastLine(models.Model):
    _inherit = 'account.treasury.forecast.line'

    payment_mode_id = fields.Many2one('account.payment.mode', string="Payment Mode")


class AccountTreasuryForecast(models.Model):
    _inherit = 'account.treasury.forecast'

    not_bank_maturity = fields.Boolean(string="Without Bank Maturities",
                                       help="It will be reflected in the treasury analysis")

    @api.multi
    def calculate_line(self):
        treasury_line_obj = self.env['account.treasury.forecast.line']
        for record in self:
            result = super(AccountTreasuryForecast, record).calculate_line()
            line_lst = treasury_line_obj.search([('treasury_id', '=', record.id)])
            for line_o in line_lst:
                payment_mode_id = line_o.template_line_id.payment_mode_id.id
                line_o.payment_mode_id = payment_mode_id
        return result

    @api.multi
    def calc_final_amount(self):
        for record in self:
            super(AccountTreasuryForecast, record).calc_final_amount()
            balance = record.final_amount
            if not record.not_bank_maturity:
                bank_maturities = self.env['bank.maturity'].search([('date_due', '>=', record.start_date),
                                                                    ('date_due', '<=', record.end_date),
                                                                    ('paid', '=', False)])
                bank_amount = sum([x.amount for x in bank_maturities])
                balance -= bank_amount
                record.final_amount = balance


class BankMaturity(models.Model):
    _name = 'bank.maturity'

    bank_account = fields.Many2one('res.partner.bank', string="Bank account",
                                   domain=lambda self: [('partner_id', '=', self.env.user.company_id.partner_id.id)])
    bank_name = fields.Char("Bank", related='bank_account.bank_name', readonly=True)
    date_due = fields.Date(string="Due Date")
    amount = fields.Float(string="Amount", digits=dp.get_precision('Account'))
    paid = fields.Boolean(string="Paid")
