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
