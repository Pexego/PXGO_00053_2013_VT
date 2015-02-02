# -*- coding: utf-8 -*-
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
from openerp import models, fields


class StockInvoiceDeposit(models.TransientModel):
    _name = 'stock.invoice.deposit'

    def _get_journal(self):
        journal_obj = self.env['account.journal']
        journals = journal_obj.search(cr, uid, [('type', '=', 'sale')])
        return journals and journals[0] or False

    journal_id = fields.Many2one('account.journal', 'Journal',
                                 default='_get_jorunal', required=True)
    date_invoice = fields.Date('Invoice date')
    group_by_sale = fields.Boolean('Group by sale')

    def create_invoice(self):
        deposit_ids = self.env.context.get('active_ids', [])
