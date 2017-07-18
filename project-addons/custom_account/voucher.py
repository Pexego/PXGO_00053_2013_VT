# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos S.L.
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

from openerp import models, fields, api, osv


class AccountVoucher(models.Model):

    _inherit = "account.voucher"

    @api.one
    def concile_all(self, context=None):
        if context['select'] == 'invoices':
            for line in self.line_cr_ids:
                res = {}
                line.reconcile = True
                amount_unreconciled = line.amount_unreconciled
                res = line.onchange_reconcile(line.reconcile, line.amount, amount_unreconciled)
                line.amount = res['value']['amount']

        elif context['select'] == 'debit':
            for line in self.line_dr_ids:
                res = {}
                line.reconcile = True
                amount_unreconciled = line.amount_unreconciled
                res = line.onchange_reconcile(line.reconcile, line.amount, amount_unreconciled)
                line.amount = res['value']['amount']

    @api.one
    def clear_all(self, context=None):
        if context['select'] == 'invoices':
            for line in self.line_cr_ids:
                res = {}
                line.reconcile = False
                amount_unreconciled = line.amount_unreconciled
                res = line.onchange_reconcile(line.reconcile, line.amount, amount_unreconciled)
                line.amount = res['value']['amount']

        elif context['select'] == 'debit':
            for line in self.line_dr_ids:
                res = {}
                line.reconcile = False
                amount_unreconciled = line.amount_unreconciled
                res = line.onchange_reconcile(line.reconcile, line.amount, amount_unreconciled)
                line.amount = res['value']['amount']

    @api.multi
    def onchange_journal(self, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        res = super(AccountVoucher, self).onchange_journal(journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None)
        voucher_line_pool = self.pool.get('account.voucher.line')
        length_cr = len(res['value']['line_cr_ids'])
        length_dr = len(res['value']['line_dr_ids'])
        cont = 0
        for voucher_line in self.line_cr_ids:
            res_id = 0
            cont_cr = length_cr / 2 - 1
            while res_id != voucher_line.id:
                res_id = res['value']['line_cr_ids'][cont][1]
                cont += 1
            cont_cr += cont
            if 'reconcile' in res['value']['line_cr_ids'][cont_cr] and not voucher_line.reconcile:
                voucher_line.reconcile = False
                voucher_line.amount = 0.0
            elif 'reconcile' not in res['value']['line_cr_ids'][cont_cr] and voucher_line.reconcile:
                voucher_line.reconcile = True
                voucher_line.amount = voucher_line.amount_unreconciled

            res['value']['line_cr_ids'][cont_cr]['amount'] = voucher_line.amount
            res['value']['line_cr_ids'][cont_cr]['reconcile'] = voucher_line.reconcile
            voucher_line_pool.write(self._cr, self._uid, [voucher_line.id], {'reconcile': voucher_line.reconcile,
                                                                             'amount': voucher_line.amount})

        cont = 0
        for voucher_line in self.line_dr_ids:
            res_id = 0
            cont_dr = length_dr / 2 - 1
            while res_id != voucher_line.id:
                res_id = res['value']['line_dr_ids'][cont][1]
                cont += 1
            cont_dr += cont
            if 'reconcile' in res['value']['line_dr_ids'][cont_dr] and not voucher_line.reconcile:
                voucher_line.reconcile = False
                voucher_line.amount = 0.0
            elif 'reconcile' not in res['value']['line_dr_ids'][cont_dr] and voucher_line.reconcile:
                voucher_line.reconcile = True
                voucher_line.amount = voucher_line.amount_unreconciled

            res['value']['line_dr_ids'][cont_dr]['amount'] = voucher_line.amount
            res['value']['line_dr_ids'][cont_dr]['reconcile'] = voucher_line.reconcile
            voucher_line_pool.write(self._cr, self._uid, [voucher_line.id], {'reconcile': voucher_line.reconcile,
                                                                             'amount': voucher_line.amount})

        return res
    
    @api.one
    def _get_amount_with_rate(self):
        self.amount_with_currency_rate = self.amount * \
            self.payment_rate

    amount_with_currency_rate = fields.Float("Rate amount",
                                             compute="_get_amount_with_rate")
