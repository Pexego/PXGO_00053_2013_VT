# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class PaymentLine(models.Model):

    _inherit = 'account.payment.line'

    is_refund = fields.Boolean(compute='_get_is_refund')
    not_change_date = fields.Boolean("Not change date")

    @api.multi
    def write(self, vals):
        if 'not_change_date' not in vals and vals.get('date'):
            for line in self:
                if line.not_change_date:
                    del vals['date']
                    break

        return super().write(vals)

    @api.multi
    def _get_is_refund(self):
        for line in self:
            line.is_refund = line.amount_currency < 0 and True or False


class AccountAccount(models.Model):

    _inherit = 'account.account'

    not_payment_followup = fields.\
        Boolean("Don't show on supplier payment follow-ups")


class AccountPayment(models.Model):

    _inherit = "account.payment"

    @api.depends('invoice_ids', 'currency_id', 'payment_date')
    def _get_current_exchange_rate(self):
        for payment in self:
            if payment.invoice_ids and payment.journal_id and \
                    payment.invoice_ids[0].currency_id != \
                    payment.journal_id.company_id.currency_id:
                payment.current_exchange_rate = payment.journal_id.company_id.\
                    currency_id.with_context(date=self.payment_date).\
                    _get_conversion_rate(payment.journal_id.
                                         company_id.currency_id,
                                         payment.invoice_ids[0].currency_id)
            else:
                payment.current_exchange_rate = 1.0

    current_exchange_rate = fields.Float("Exchange rate computed",
                                         compute="_get_current_exchange_rate",
                                         digits=(16, 6), readonly=True,
                                         help="Currency rate used to convert "
                                              "to company currency")
    force_exchange_rate = fields.Float("Force exchange rate", digits=(16, 6))

    @api.multi
    def post(self):
        for rec in self:
            ctx = self.env.context.copy()
            if rec.invoice_ids and \
                    all([x.currency_id == rec.invoice_ids[0].currency_id
                         for x in rec.invoice_ids]):
                invoice_currency = rec.invoice_ids[0].currency_id
                if invoice_currency != \
                        rec.invoice_ids[0].company_id.currency_id and \
                        rec.force_exchange_rate:
                    ctx['force_from_rate'] = rec.force_exchange_rate
            super(AccountPayment, rec.with_context(ctx)).post()
        return True
