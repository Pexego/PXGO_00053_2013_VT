# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
from openerp import models, fields, api, exceptions, SUPERUSER_ID


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    cost_unit = fields.Float("Product cost price")


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    subtotal_wt_rect = fields.Float("Subtotal",
                                    compute="get_subtotal_wt_rect", store=True)
    total_wt_rect = fields.Float("Total",
                                 compute="get_total_wt_rect", store=True)

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for inv in self:
            for line in inv.invoice_line_ids:
                line.write({'cost_unit': line.product_id.standard_price})
        return res

    @api.multi
    @api.depends('type', 'amount_untaxed')
    def get_subtotal_wt_rect(self):
        for invoice in self:
            if 'refund' in invoice.type:
                invoice_wt_rect = -invoice.amount_untaxed
            else:
                invoice_wt_rect = invoice.amount_untaxed

            invoice.subtotal_wt_rect = invoice_wt_rect

    @api.multi
    @api.depends('type', 'amount_total')
    def get_total_wt_rect(self):
        for invoice in self:
            if 'refund' in invoice.type:
                invoice_wt_rect = - invoice.amount_total
            else:
                invoice_wt_rect = invoice.amount_total

            invoice.total_wt_rect = invoice_wt_rect
