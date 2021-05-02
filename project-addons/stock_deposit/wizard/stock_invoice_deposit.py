##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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


class StockInvoiceDeposit(models.TransientModel):
    _name = 'stock.invoice.deposit'

    def _get_journal(self):
        journal_obj = self.env['account.journal']
        deposit_obj = self.env['stock.deposit']
        deposits = deposit_obj.browse(self._context['active_ids'])
        sale_invoice_types = deposits.mapped('sale_id.invoice_type_id')
        if len(sale_invoice_types.mapped('journal_id')) > 1 \
                or (sale_invoice_types.mapped('journal_id')
                    and sale_invoice_types.filtered(lambda d: not d.journal_id)):
            raise exceptions.Warning(_('There are two or more different account journals. '
                                       'Please, make sure to select sale orders with the same journal.'))
        elif deposits.mapped('sale_id.invoice_type_id.journal_id'):
            journals = deposits.mapped('sale_id.invoice_type_id.journal_id')
        else:
            journals = journal_obj.search([('type', '=', 'sale')])
        return journals and journals[0] or False

    journal_id = fields.Many2one('account.journal', 'Destination Journal',
                                 required=True, default=_get_journal)

    @api.multi
    def create_invoice(self):
        deposit_obj = self.env['stock.deposit']
        deposit_ids = self.env.context['active_ids']
        deposits = deposit_obj.search([('id', 'in', deposit_ids),
                                       ('state', '=', 'sale')])
        if not deposits:
            raise exceptions.Warning(_('No deposit selected'))
        invoice_ids = deposits.create_invoice(self.journal_id)
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action['domain'] = \
            "[('id','in', [" + ','.join(map(str, invoice_ids)) + "])]"
        return action
