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

from openerp import models, fields, api


class ResPartner(models.Model):

    _inherit = "res.partner"

    @api.one
    def _get_on_account_amount(self):
        amount = 0.0
        voucher_obj = self.env["account.voucher"]
        move_line_obj = self.env["account.move.line"]
        voucher_ids = voucher_obj.search([("type", "=", "receipt"),
                                          ("sale_id", "!=", False),
                                          ("sale_id.state", "=", "cancel"),
                                          ("partner_id", "=",
                                           self.id)])
        move_ids = []
        for voucher in voucher_ids:
            for move in voucher.move_ids:
                if move.account_id.type in ('receivable', 'payable') and \
                        not move.reconcile_id:
                    move_ids.append(move.id)
                    if move.reconcile_partial_id:
                        amount += move.amount_residual_currency > 0 and \
                            move.amount_residual_currency or 0.0
                    else:
                        amount += abs(move.amount_currency) or move.credit

        moves = move_line_obj.search([('id', 'not in', move_ids),
                                      ('partner_id', '=', self.id),
                                      ('credit', '>', 0.0),
                                      ('reconcile_id', '=', False),
                                      ('account_id.type', '=', 'receivable')])

        for move in moves:
            vouchers = voucher_obj.search([('move_id', '=', move.move_id.id),
                                           ('sale_id', '!=', False)])
            if not vouchers:
                if move.reconcile_partial_id:
                    amount += move.amount_residual_currency > 0 and \
                        move.amount_residual_currency or 0.0
                else:
                    amount += abs(move.amount_currency) or move.credit

        self.on_account_amount = amount

    on_account_amount = fields.Float("On account amount", readonly=True,
                                     compute="_get_on_account_amount")
