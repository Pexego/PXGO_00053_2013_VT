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


class ApplyOnAccountAmount(models.TransientModel):

    _name = "apply.on.account.amount"

    amount = fields.Float("Amount to apply", required=True)

    @api.multi
    def apply_amount(self):
        invoice_obj = self.env["account.invoice"]
        invoice = invoice_obj.browse(self.env.context["active_ids"][0])
        if invoice.on_account_amount < self[0].amount:
            raise exceptions.Warning(_("Cannot apply more amount that current"
                                       " on account amount"))
        elif self[0].amount <= 0:
            raise exceptions.Warning(_("Cannot apply a negative amount"))

        voucher_obj = self.env["account.voucher"]
        move_line_obj = self.env["account.move.line"]
        moves = self.env["account.move.line"]
        voucher_ids = voucher_obj.search([("type", "=", "receipt"),
                                          ("sale_id", "!=", False),
                                          ("sale_id.state", "=", "cancel"),
                                          ("partner_id", "=",
                                           invoice.partner_id.id)])

        for voucher in voucher_ids:
            for move in voucher.move_ids:
                if move.account_id.type in ('receivable', 'payable') and \
                        not move.reconcile_id and \
                        (not move.reconcile_partial_id or
                         move.amount_residual_currency > 0):
                    moves += move

        moves2 = move_line_obj.search([('id', 'not in',
                                       [x.id for x in moves]),
                                      ('partner_id', '=',
                                       invoice.partner_id.id),
                                      ('credit', '>', 0.0),
                                      ('reconcile_id', '=', False),
                                      ('account_id.type', '=', 'receivable')])
        for move2 in moves2:
            vouchers = voucher_obj.search([('move_id', '=',
                                            move2.move_id.id),
                                           ('sale_id', '!=', False)])
            if not vouchers:
                moves += move2

        partial_moves = moves.filtered(lambda x: x.reconcile_partial_id)
        complete_moves = moves.filtered(lambda x: not x.reconcile_partial_id)
        complete_moves.sorted(key=lambda x: x.credit)

        select_moves = self.env["account.move.line"]
        amount = self[0].amount
        last_move = False
        for move in complete_moves:
            if (abs(move.amount_currency) or move.credit) <= amount:
                select_moves += move
                amount -= abs(move.amount_currency) or move.credit
            else:
                last_move = move

        if amount > 0 and last_move:
            select_moves += last_move
        elif amount > 0:
            partial_moves.sorted(key=lambda x: x.amount_residual_currency)
            for move in partial_moves:
                if move.amount_residual_currency <= amount:
                    select_moves += move
                    amount -= move.amount_residual_currency
                else:
                    last_move = move

        if amount > 0 and last_move:
            select_moves += last_move

        if moves:
            moves += move_line_obj.search([('move_id', '=',
                                            invoice.move_id.id),
                                           ('account_id', '=',
                                            invoice.account_id.id)])
            try:
                moves.reconcile_partial(type='manual')
            except Exception:
                pass

        return True
