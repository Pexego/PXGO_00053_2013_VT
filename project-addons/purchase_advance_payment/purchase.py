# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
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


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    @api.one
    def _get_amount_residual(self):
        advance_amount = 0.0
        for line in self.account_voucher_ids:
            if line.state == 'posted':
                advance_amount += round(line.amount * line.payment_rate, 2)
        self.amount_resisual = self.amount_total - advance_amount

    account_voucher_ids = fields.One2many('account.voucher', 'purchase_id',
                                          string="Pay purchase advanced",
                                          readonly=True)
    amount_resisual = fields.Float('Residual amount', readonly=True,
                                   compute="_get_amount_residual")
