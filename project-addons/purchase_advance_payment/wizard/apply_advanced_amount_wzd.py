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
import time


class ApplyOnAccountPurchaseAmount(models.TransientModel):

    _name = "apply.on.account.purchase.amount"

    amount = fields.Float("Amount to apply", required=True)
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)

    @api.model
    def default_get(self, fields):
        res = super(ApplyOnAccountPurchaseAmount, self).default_get(fields)
        invoice_ids_ids = self.env.context.get('active_ids', [])
        if not invoice_ids_ids:
            return res
        invoice_id = invoice_ids_ids[0]

        invoice = self.env['account.invoice'].browse(invoice_id)

        amount = invoice.on_account_purchase

        if 'amount' in fields:
            res.update({'amount': amount,
                        'currency_id': invoice.currency_id.id})

        return res

    @api.model
    def _get_account_voucher_line(self, voucher, line):
        voucher_line_obj = self.env["account.voucher.line"]
        company_currency = line.move_id.company_id.currency_id
        amount_original = abs(line.amount_currency)
        amount_unreconciled = abs(line.amount_residual_currency)

        vals = {'name': line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id': line.id,
                'account_id': line.account_id.id,
                'amount_original': amount_original,
                'amount': 0.0,
                'date_original': line.date,
                'date_due': line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': company_currency.id,
                'voucher_id': voucher.id}
        return voucher_line_obj.create(vals)

    @api.multi
    def apply_amount(self):
        invoice_obj = self.env["account.invoice"]
        invoice = invoice_obj.browse(self.env.context["active_ids"][0])
        invoice_currency = invoice.currency_id
        company_currency = invoice.company_id.currency_id
        if invoice.on_account_purchase < self[0].amount:
            raise exceptions.Warning(_("Cannot apply more amount that current"
                                       " on account amount"))
        elif self[0].amount <= 0:
            raise exceptions.Warning(_("Cannot apply a negative amount"))
        elif self[0].amount > invoice.residual:
            raise exceptions.Warning(_("Cannot apply more amount than "
                                       "residual on invoice."))

        voucher_obj = self.env["account.voucher"]
        move_line_obj = self.env["account.move.line"]
        moves = self.env["account.move.line"]
        period_obj = self.env["account.period"]

        move_lines = move_line_obj.\
            search([('move_id', '=', invoice.move_id.id),
                    ('account_id', '=', invoice.account_id.id)])

        voucher_ids = voucher_obj.search([("type", "=", "payment"),
                                          ("purchase_id", "!=", False),
                                          ("purchase_id.state", "=", "cancel"),
                                          ("partner_id", "=",
                                           invoice.partner_id.id)])

        for voucher in voucher_ids:
            for move in voucher.move_ids:
                if move.account_id.internal_type in ('receivable', 'payable') and \
                        not move.full_reconcile_id and \
                        (not move.reconcile_partial_id or
                         move.amount_residual_currency > 0):
                    moves += move

        moves2 = move_line_obj.search([('id', 'not in',
                                       [x.id for x in moves]),
                                      ('partner_id', '=',
                                       invoice.partner_id.id),
                                      ('debit', '>', 0.0),
                                      ('full_reconcile_id', '=', False),
                                      ('account_id.internal_type', '=', 'payable')])
        for move2 in moves2:
            vouchers = voucher_obj.search([('move_id', '=',
                                            move2.move_id.id),
                                           ('purchase_id', '!=', False)])
            if not vouchers and move2.amount_residual_currency > 0 :
                moves += move2

        journal_id = self[0].journal_id

        date = time.strftime("%Y-%m-%d")
        period_ids = period_obj.find(date)
        period_id = period_ids[0]

        amount = self[0].amount
        select_moves = []

        moves.sorted(key=lambda x: x.reconcile_partial_id)
        for move in moves:
            if not amount:
                continue
            if (move.currency_id and move.currency_id == invoice_currency) or\
                    (not move.currency_id and invoice_currency ==
                     company_currency):
                if abs(move.amount_residual_currency) <= amount:
                    select_moves.append((move,
                                         abs(move.amount_residual),
                                         True))
                    amount -= abs(move.amount_residual_currency)
                else:
                    if move.currency_id:
                        exchange_rate = abs(move.amount_currency) / \
                            (move.debit or move.credit)
                    else:
                        exchange_rate = 1.0
                    select_moves.append((move, amount / exchange_rate,
                                         False))
                    amount = 0.0
            elif move.currency_id:
                if abs(move.amount_residual) <= amount:
                    select_moves.append((move, abs(move.amount_residual),
                                         True))
                    amount -= abs(move.amount_residual)
                else:
                    exchange_rate = abs(move.amount_currency) / \
                        (move.debit or move.credit)
                    select_moves.append((move, amount / exchange_rate, False))
                    amount = 0.0
            elif not move.currency_id:
                cur_amount = company_currency.\
                    compute(abs(move.amount_residual), invoice_currency)
                if cur_amount <= amount:
                    select_moves.append((move, abs(move.amount_residual),
                                         True))
                    amount -= cur_amount
                else:
                    select_moves.append((move, amount, False))
                    amount = 0.0

        for move in select_moves:
            multicurrency = False
            exchange_rate = 1.0
            if move[0].amount_currency:
                multicurrency = True
                exchange_rate = abs(move[0].amount_currency) / \
                    (move[0].debit or move[0].credit)
                currency_id = move[0].currency_id.id
            else:
                currency_id = invoice.company_id.currency_id.id
            voucher = voucher_obj.\
                create({'type': 'payment',
                        'partner_id': invoice.partner_id.id,
                        'journal_id': journal_id.id,
                        'pre_line': True,
                        'account_id': invoice.account_id.id,
                        'company_id': invoice.company_id.id,
                        'payment_rate_currency_id': currency_id,
                        'payment_rate': exchange_rate,
                        'date': date,
                        'amount': 0.0,
                        'is_multi_currency': multicurrency,
                        'period_id': period_id.id,
                        'name': _("On account Payment")})
            line = self._get_account_voucher_line(voucher, move_lines[0])
            if move[1] == abs(move_lines[0].amount_residual):
                line.reconcile = True
                line.amount = abs(move_lines[0].amount_residual)
            else:
                line.amount = move[1]
            line2 = self._get_account_voucher_line(voucher, move[0])
            line2.reconcile = move[2]
            line2.amount = move[1]

            voucher.signal_workflow('proforma_voucher')

        return True
