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

from openerp import models, fields, api


class AccountVoucher(models.Model):

    _inherit = "account.voucher"

    @api.one
    def _get_amount_with_rate(self):
        self.amount_with_currency_rate = self.amount * \
            self.payment_rate

    amount_with_currency_rate = fields.Float("Rate amount",
                                             compute="_get_amount_with_rate")

    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id,
                                price, currency_id, ttype, date, context=None):
        res = super(AccountVoucher, self).\
            recompute_voucher_lines(cr, uid, ids, partner_id, journal_id,
                                    price, currency_id, ttype, date,
                                    context=context)
        if res.get('value', False) and 'line_cr_ids' in res['value']:
            for line_rec in res['value']['line_cr_ids']:
                line_rec['amount'] = 0.0
                line_rec['reconcile'] = False
        if res.get('value', False) and 'line_dr_ids' in res['value']:
            for line_rec in res['value']['line_dr_ids']:
                line_rec['amount'] = 0.0
                line_rec['reconcile'] = False

        return res
