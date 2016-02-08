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


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.one
    def _get_advance_amount(self):
        orders = []
        amount = 0.0
        for line in self.invoice_line:
            if line.move_id and line.move_id.procurement_id and \
                    line.move_id.procurement_id.sale_line_id:
                sale = line.move_id.procurement_id.sale_line_id.order_id
                if sale not in orders:
                    orders.append(sale)
                    for vline in sale.account_voucher_ids:
                        if vline.state != 'posted':
                            continue
                        for move in vline.move_ids:
                            if move.account_id.type in ('receivable',
                                                        'payable'):
                                if move.reconcile_partial_id:
                                    amount += move.amount_residual > 0 and \
                                        move.amount_residual or 0.0
                                elif move.reconcile_id:
                                    continue
                                else:
                                    amount += move.credit
        self.advance_amount = amount

    @api.one
    def _get_on_account_amount(self):
        self.on_account_amount = self.partner_id.on_account_amount

    advance_amount = fields.Float("Advance amount", readonly=True,
                                  compute="_get_advance_amount")
    on_account_amount = fields.Float("On account amount", readonly=True,
                                     compute="_get_on_account_amount")

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        move_line_obj = self.env["account.move.line"]
        move_lines = self.env["account.move.line"]
        for invoice in self:
            orders = []
            for line in invoice.invoice_line:
                if line.move_id and line.move_id.procurement_id and \
                        line.move_id.procurement_id.sale_line_id:
                    sale = line.move_id.procurement_id.sale_line_id.order_id
                    if sale not in orders:
                        if sale.account_voucher_ids:
                            orders.append(sale)
            if orders:
                move_lines = move_line_obj.\
                    search([('move_id', '=', invoice.move_id.id),
                            ('account_id', '=', invoice.account_id.id)])

                for sale_order in orders:
                    for payment in sale_order.account_voucher_ids:
                        if payment.state != 'posted':
                            continue
                        payment.move_id.post()
                        for line in payment.move_ids:
                            if line.account_id.id == invoice.account_id.id:
                                move_lines += line
                try:
                    if move_lines:
                        move_lines.reconcile_partial(type='manual')
                except Exception:
                    pass
        return res
