##############################################################################
#
#    Copyright 2013 Camptocamp
#    Copyright 2009-2013 Akretion,
#    Author: Emmanuel Samyn, Raphaël Valyi, Sébastien Beau,
#            Benoît Guillot, Joel Grand-Guillaume
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
from odoo import models, _, exceptions, fields


class AccountInvoiceRefund(models.TransientModel):

    _inherit = "account.invoice.refund"

    def compute_refund(self, cr, uid, ids, mode='refund', context=None):
        if context is None:
            context = {}
        if context.get('invoice_ids', []) and context.get('invoice_ids')[0]:
            context['active_ids'] = context.get('invoice_ids')
        elif context['active_model'] == u'crm.claim':
            raise exceptions.UserError(_('The claim not have invoices to refund.'))
        return super(AccountInvoiceRefund, self).compute_refund(
            cr, uid, ids, mode=mode, context=context)

    def _get_description(self, cr, uid, context=None):
        if context is None:
            context = {}
        description = context.get('description') or ''
        return description

    description = fields.Text(default=_get_description)
