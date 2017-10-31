# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea (<http://www.comunitea.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp import models, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.model
    def _prepare_invoice(self, order, lines):
        """Copy bank partner from sale order to invoice"""
        vals = super(SaleOrder, self)._prepare_invoice(order, lines)
        if order.payment_mode_id and order.payment_mode_id.payment_order_type == "debit":
            invoice_partner = order.partner_id.commercial_partner_id
            mandate_obj = self.env["account.banking.mandate"]
            mandates = mandate_obj.search(
                [('partner_bank_id', 'in', invoice_partner.bank_ids.ids),
                 ('default', '=', True),
                 ('state', '=', 'valid')])
            mandate_sel = False
            if mandates:
                mandate_sel = mandates[0]
            else:
                mandates = mandate_obj.search(
                    [('partner_bank_id', 'in',
                      invoice_partner.bank_ids.ids),
                     ('state', '=', 'valid')])
                if mandates:
                    mandate_sel = mandates[0]
            if mandate_sel:
                vals['mandate_id'] = mandate_sel.id
                vals['partner_bank_id'] = mandate_sel.partner_bank_id.id
            elif invoice_partner.bank_ids:
                vals['partner_bank_id'] = invoice_partner.bank_ids[0].id
        if 'comment' in vals:
            vals.pop('comment', None)
        return vals

