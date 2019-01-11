# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class PaymentLine(models.Model):

    _inherit = 'account.payment.line'

    is_refund = fields.Boolean(compute='_get_is_refund')

    @api.multi
    def _get_is_refund(self):
        for line in self:
            line.is_refund = line.amount_currency < 0 and True or False


class AccountAccount(models.Model):

    _inherit = 'account.account'

    not_payment_followup = fields.Boolean("Don't show on supplier payment follow-ups")
