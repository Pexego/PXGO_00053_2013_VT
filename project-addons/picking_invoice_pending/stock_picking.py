# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time


class StockPicking(models.Model):

    _inherit = "stock.picking"

    pending_invoice_move_id = fields.Many2one('account.move',
                                              'Account pending move',
                                              readonly=True,
                                              copy=False)
    pending_stock_reverse_move_id = \
        fields.Many2one('account.move', 'Account pending stock reverse move',
                        readonly=True, copy=False)
    pending_stock_move_id = \
        fields.Many2one('account.move', 'Account pending stock move',
                        readonly=True, copy=False)

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        for pick in self:
            if not pick.date_done:
                pick.date_done = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return res

    @api.multi
    def account_pending_invoice(self, debit_account, credit_account, date):
        self.ensure_one()
        period_obj = self.env['account.period']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        lines = {}

        period_id = period_obj.find(date)

        origin = self.name
        if self.origin:
            origin += ':' + self.origin

        stock_journal_id = self.company_id.property_pending_stock_journal.id

        move = {
            'ref': origin,
            'journal_id': stock_journal_id,
            'period_id': period_id.id,
            'date': date,
        }
        move_id = move_obj.create(move)
        obj_precision = self.env['decimal.precision']
        for move_line in self.move_lines:
            name = move_line.name or origin

            amount_line = round(move_line.price_unit, obj_precision.
                                precision_get('Account')) * \
                move_line.product_qty
            vals = {
                'name': name,
                'ref': origin,
                'partner_id': move_line.partner_id.commercial_partner_id.id,
                'product_id': move_line.product_id.id,
                'account_id': debit_account.id,
                'debit': amount_line,
                'credit': 0,
                'quantity': move_line.product_qty,
                'move_id': move_id.id,
                'journal_id': stock_journal_id,
                'period_id': period_id.id,
            }
            move_line_obj.create(vals)
            if move_line.partner_id.commercial_partner_id.id in lines:
                lines[move_line.partner_id.commercial_partner_id.id] += \
                    amount_line
            else:
                lines[move_line.partner_id.commercial_partner_id.id] = \
                    amount_line

        for partner_id in lines:
            vals = {
                'name': name,
                'ref': origin,
                'partner_id': partner_id,
                'account_id': credit_account.id,
                'debit': 0,
                'credit': round(lines[partner_id], obj_precision.
                                precision_get('Account')),
                'move_id': move_id.id,
                'journal_id': stock_journal_id,
                'period_id': period_id.id,
            }
            move_line_obj.create(vals)
        move_id.post()

        return move_id

    @api.multi
    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if vals.get('date_done', False):
            for pick in self:
                if (pick.picking_type_id.code == "incoming" and pick.move_lines
                        and pick.move_lines[0].purchase_line_id and
                        pick.invoice_state in ['invoiced', '2binvoiced'] and
                        pick.company_id.required_invoice_pending_move):
                    pick.refresh()
                    if not pick.company_id.\
                            property_pending_variation_account or not \
                            pick.company_id.property_pending_stock_account:
                        raise Warning(_("You need to configure the accounts "
                                        "in the company for pending invoices"))
                    if not pick.company_id.property_pending_stock_journal:
                        raise Warning(_("You need to configure an account "
                                        "journal in the company for pending "
                                        "invoices"))
                    debit_account = pick.company_id.\
                        property_pending_variation_account
                    credit_account = pick.company_id.\
                        property_pending_stock_account
                    move_id = pick.account_pending_invoice(debit_account,
                                                           credit_account,
                                                           vals['date_done'])
                    pick.pending_stock_reverse_move_id = move_id.id
        return res

    @api.multi
    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        pick = self[0]
        if not pick.company_id.\
                property_pending_variation_account or not \
                pick.company_id.property_pending_stock_account or not \
                pick.company_id.property_pending_supplier_invoice_account:
            raise Warning(_("You need to configure the accounts "
                            "in the company for pending invoices"))
        if not pick.company_id.property_pending_stock_journal:
            raise Warning(_("You need to configure an account "
                            "journal in the company for pending "
                            "invoices"))
        for pick in self:
            if pick.picking_type_id.code == "incoming" and pick.move_lines \
                    and pick.move_lines[0].purchase_line_id and \
                    pick.invoice_state in ['invoiced', '2binvoiced'] and \
                    pick.company_id.required_invoice_pending_move:
                debit_account = pick.company_id.\
                    property_pending_expenses_account
                credit_account = pick.company_id.\
                    property_pending_supplier_invoice_account
                move_id = pick.account_pending_invoice(debit_account,
                                                       credit_account,
                                                       pick.create_date[:10])
                pick.pending_invoice_move_id = move_id.id

                debit_account = pick.company_id.\
                    property_pending_stock_account
                credit_account = pick.company_id.\
                    property_pending_variation_account
                move_id = pick.account_pending_invoice(debit_account,
                                                       credit_account,
                                                       pick.create_date[:10])
                pick.pending_stock_move_id = move_id.id

        return res

    @api.multi
    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        for pick in self:
            if pick.pending_stock_move_id:
                pick.pending_stock_move_id.button_cancel()
                pick.pending_stock_move_id.unlink()
            if pick.pending_invoice_move_id:
                pick.pending_invoice_move_id.button_cancel()
                pick.pending_invoice_move_id.unlink()
            if pick.pending_stock_reverse_move_id:
                pick.pending_stock_reverse_move_id.button_cancel()
                pick.pending_stock_reverse_move_id.unlink()
        return res

    @api.multi
    def unlink(self):
        for pick in self:
            if pick.pending_stock_move_id:
                pick.pending_stock_move_id.button_cancel()
                pick.pending_stock_move_id.unlink()
            if pick.pending_invoice_move_id:
                pick.pending_invoice_move_id.button_cancel()
                pick.pending_invoice_move_id.unlink()
            if pick.pending_stock_reverse_move_id:
                pick.pending_stock_reverse_move_id.button_cancel()
                pick.pending_stock_reverse_move_id.unlink()
        res = super(StockPicking, self).unlink()
        return res
