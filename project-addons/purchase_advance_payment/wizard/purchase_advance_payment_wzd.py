# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saaevdra <omar@comunitea.com>$
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

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class AccountVoucherWizard(models.TransientModel):

    _name = "account.purchase.voucher.wizard"

    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    amount_total = fields.Float('Amount total', readonly=True)
    amount_advance = fields.Float('Amount advanced', required=True,
                                  digits_compute=
                                  dp.get_precision('Sale Price'))
    date = fields.Date("Date", required=True,
                       default=fields.Date.context_today)
    exchange_rate = fields.Float("Exchange rate", digits=(16, 6), default=1.0,
                                 required=True)
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)
    currency_amount = fields.Float("Curr. amount", digits=(16, 2),
                                   readonly=True)

    @api.constrains('amount_advance')
    def check_amount(self):
        if self.amount_advance <= 0:
            raise exceptions.ValidationError(_("Amount of advance must be "
                                               "positive."))
        if self.env.context.get('active_id', False):
            order = self.env["purchase.order"].\
                browse(self.env.context['active_id'])
            if self.amount_advance > order.amount_resisual:
                raise exceptions.ValidationError(_("Amount of advance is "
                                                   "greater than residual "
                                                   "amount on purchase"))

    @api.model
    def default_get(self, fields):
        res = super(AccountVoucherWizard, self).default_get(fields)
        purchase_ids = self.env.context.get('active_ids', [])
        if not purchase_ids:
            return res
        purchase_id = purchase_ids[0]

        purchase = self.env['purchase.order'].browse(purchase_id)

        amount_total = purchase.amount_total

        if 'amount_total' in fields:
            res.update({'amount_total': amount_total,
                        'currency_id': purchase.currency_id.id})

        return res

    @api.onchange('journal_id','date')
    def onchange_date(self):
        if self.currency_id:
            self.exchange_rate = 1.0 / \
                (self.env["res.currency"].with_context(date=self.date).
                 _get_conversion_rate(self.currency_id,
                                      (self.journal_id.currency or
                                      self.env.user.company_id.
                                      currency_id))
                 or 1.0)
            self.currency_amount = self.amount_advance * \
                (1.0 / self.exchange_rate)
        else:
            self.exchange_rate = 1.0

    @api.onchange('exchange_rate', 'amount_advance')
    def onchange_amount(self):
        self.currency_amount = self.amount_advance * (1.0 / self.exchange_rate)

    @api.multi
    def make_advance_payment(self):
        """Create customer paylines and validates the payment"""
        voucher_obj = self.env['account.voucher']
        purchase_obj = self.env['purchase.order']
        period_obj = self.env['account.period']

        purchase_ids = self.env.context.get('active_ids', [])
        if purchase_ids:
            purchase_id = purchase_ids[0]
            purchase = purchase_obj.browse(purchase_id)

            partner_id = purchase.partner_id.id
            date = self[0].date
            company_id = purchase.company_id.id
            purchase_ref = purchase.id
            period_ids = period_obj.find(date)
            period_id = period_ids[0]
            if purchase.currency_id.id != self[0].journal_id.currency.id and \
                    purchase.currency_id.id != \
                    self[0].journal_id.company_id.currency_id.id:
                multicurrency = True
                currency_amount = self[0].amount_advance * \
                    1.0 / (self[0].exchange_rate or 1.0)
            else:
                multicurrency = False
                currency_amount = self[0].amount_advance

            voucher_res = {'type': 'payment',
                           'partner_id': partner_id,
                           'journal_id': self[0].journal_id.id,
                           'account_id':
                           self[0].journal_id.default_credit_account_id.id,
                           'company_id': company_id,
                           'payment_rate_currency_id': purchase.currency_id.id,
                           'payment_rate': multicurrency and
                           self[0].exchange_rate or 1.0,
                           'date': date,
                           'amount': currency_amount,
                           'is_multi_currency': multicurrency,
                           'period_id': period_id.id,
                           'purchase_id': purchase_ref,
                           'name': _("Advance Payment"),
                           'reference': purchase.name
                           }
            voucher = voucher_obj.create(voucher_res)
            voucher.action_move_line_create()
            voucher.refresh()
            if multicurrency:
                for line in voucher.move_ids:
                    line.currency_id = self[0].currency_id.id
                    if line.credit:
                        line.amount_currency = -self[0].amount_advance
                    else:
                        line.amount_currency = self[0].amount_advance

            return {
                'type': 'ir.actions.act_window_close',
            }
