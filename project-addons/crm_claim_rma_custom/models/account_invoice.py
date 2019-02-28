##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from odoo import models, fields, api, exceptions, _


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        if 'state' in vals.keys():
            if vals['state'] == 'paid':
                for invoice in self:
                    invoice_line_ids = [x.id for x in invoice.invoice_line_ids]
                    substate_id = self.env.ref(
                        'crm_claim_rma_custom.substate_refund').id
                    claim_lines = self.env['claim.line'].search(
                        [('refund_line_id', 'in', invoice_line_ids)])
                    claim_lines.write({'substate_id': substate_id})
        return res
