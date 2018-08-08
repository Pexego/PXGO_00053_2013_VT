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


class AccountVoucherLine(models.Model):

    _inherit = "account.voucher.line"

    invoice = fields.Many2one('account.invoice', readonly=True, related='move_line_id.invoice')


class AccountVoucher(models.Model):

    _inherit = "account.voucher"

    line_cr_ids = fields.One2many('account.voucher.line', 'voucher_id', 'Credits',
                                  domain=['&', ('account_id.not_payment_followup', '=', False), ('type', '=', 'cr')],
                                  context={'default_type': 'cr'}, readonly=True,
                                  states={'draft': [('readonly', False)]})
    line_dr_ids = fields.One2many('account.voucher.line', 'voucher_id', 'Debits',
                                  domain=['&', ('account_id.not_payment_followup', '=', False), ('type', '=', 'dr')],
                                  context={'default_type': 'dr'}, readonly=True,
                                  states={'draft': [('readonly', False)]})

    @api.one
    def concile_all(self):
        objs = None
        if self.env.context['select'] == 'invoices':
            objs = self.line_cr_ids
        elif self.env.context['select'] == 'debit':
            objs = self.line_dr_ids

        for line in objs:
            res = {}
            line.reconcile = True
            amount_unreconciled = line.amount_unreconciled
            res = line.onchange_reconcile(line.reconcile, line.amount, amount_unreconciled)
            line.amount = res['value']['amount']

    @api.one
    def clear_all(self):
        objs = None
        if self.env.context['select'] == 'invoices':
            objs = self.line_cr_ids
        elif self.env.context['select'] == 'debit':
            objs = self.line_dr_ids

        for line in objs:
            res = {}
            line.reconcile = False
            amount_unreconciled = line.amount_unreconciled
            res = line.onchange_reconcile(line.reconcile, line.amount, amount_unreconciled)
            line.amount = res['value']['amount']

    @api.multi
    def onchange_journal(self, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        res = super(AccountVoucher, self).onchange_journal(journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None)
        if not res or not res.get('value'):
            return res
        voucher_line_pool = self.pool.get('account.voucher.line')
        length_cr = len(res['value'].get('line_cr_ids', []))
        length_dr = len(res['value'].get('line_dr_ids', []))
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

    """@api.multi
    def onchange_date(self, date, currency_id, payment_rate_currency_id, amount, company_id, context=None):
        res = super(AccountVoucher, self).onchange_date(date, currency_id, payment_rate_currency_id,
                                                           amount, company_id, context=None)
        voucher_line_pool = self.pool.get('account.voucher.line')
        res['value']['line_dr_ids'] = []
        res['value']['line_cr_ids'] = []
        cont_ids = len(self.line_ids) / 2 - 1
        cont_data = len(self.line_ids) / 2
        iterator = 0
        for line in self.line_ids:
            if line.reconcile:
                pos_ids = cont_ids - iterator
                pos_data = cont_data + iterator
                iterator += 1
                dict = {'date_due': line.move_line_id.date_maturity, 'reconcile': line.reconcile,
                        'date_original': line.move_line_id.date, 'currency_id': line.move_line_id.currency_id.id,
                        'amount_unreconciled': line.amount_unreconciled, 'account_id': line.account_id.id,
                        'move_line_id': line.move_line_id.id, 'amount_original': line.amount_original,
                        'amount': line.amount, 'type': line.type}
                if line.name:
                    dict['name'] = line.name

                if line.type == 'cr':
                    res['value']['line_cr_ids'].insert(pos_ids, (2, line.id))
                    res['value']['line_cr_ids'].insert(pos_data, dict)
                    voucher_line_pool.write(self._cr, self._uid, [line.id],
                                            {'reconcile': line.reconcile,
                                             'amount': line.amount})
                else:
                    res['value']['line_dr_ids'].insert(pos_ids, (2, line.id))
                    res['value']['line_dr_ids'].insert(pos_data, dict)
                    voucher_line_pool.write(self._cr, self._uid, [line.id],
                                            {'reconcile': line.reconcile,
                                             'amount': line.amount})

        period_ids = self.pool['account.period'].find(self.env.cr, self.env.uid, dt=date, context=dict(context, company_id=company_id))
        currency_id = False
        if self.journal_id.currency:
            currency_id = self.journal_id.currency.id
        else:
            currency_id = self.journal_id.company_id.currency_id.id
        res['value'].update({
            'currency_id': currency_id,
            'payment_rate_currency_id': currency_id,
            'period_id': period_ids and period_ids[0] or False
        })
        if self.partner_id:
            vals = self.onchange_partner_id(self.partner_id.id, self.journal_id.id, amount, currency_id, self.type, date, context=None)
            for key in vals.keys():
                res[key].update(vals[key])

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

        currency_id = False
        if self.journal_id.currency:
            currency_id = self.journal_id.currency.id
        else:
            currency_id = self.journal_id.company_id.currency_id.id

        res['value']['currency_id'] = currency_id
        res['value']['pre_line'] = 1
        return res
    """


    @api.one
    def _get_amount_with_rate(self):
        self.amount_with_currency_rate = self.amount * \
            self.payment_rate

    amount_with_currency_rate = fields.Float("Rate amount",
                                             compute="_get_amount_with_rate")

    @api.multi
    def action_move_line_create(self):
        res = super(AccountVoucher, self).action_move_line_create()

        if 'RCONF' in self.journal_id.code or 'RPAG' in self.journal_id.code:
            lines = self.mapped('move_ids')
            for line in lines:
                if not line.reconcile_ref:
                    line.write({'blocked': True})

        return res
