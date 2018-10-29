# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sánchez <kiko@comunitea.com>$
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

from openerp import models, fields, api, exceptions, _
from datetime import datetime, time
from openerp.exceptions import ValidationError
import openerp.addons.decimal_precision as dp


class product_devaluation_account_wizard(models.TransientModel):
    _name = 'product.devaluation.account.wizard'

    name = fields.Char('Account Ref', readonly=True, default=lambda self:
    self.env['product.devaluation'].browse(self.env.context.get('active_ids', False))[0].product_id.name)
    account_move_id = fields.Integer("Account ID")
    #TODO: Migrar
    #period_id = fields.Many2one('account.period', 'Period', default=lambda self:
    #    self.env['account.period'].find(time())[0].id)
    journal_id = fields.Many2one('account.journal', 'Journal', default=lambda self:
        self.env['product.devaluation'].browse(self.env.context.get('active_ids', False))[0].
        product_id.categ_id.devaluation_journal_id or self.env.user.company_id.devaluation_journal_id, required=True)
    date = fields.Date("Date", required=True,
                       default=fields.Date.context_today)

    @api.multi
    def create_dev_account(self):

        product_devaluation = self.env['product.devaluation']
        context_pool = self.env.context.get('active_ids', False)
        lines = product_devaluation.search([('id', 'in', context_pool), ('accounted_ok', '=', False)],
                                           order='product_id, date_dev asc')

        if len(lines) == 0:
            raise ValidationError(_("Please, select lines not accounted"))

        account_pool = self.env['account.move']
        period_id = self.period_id.id
        journal_id = self.journal_id.id
        company = self.env.user.company_id

        ref = self.journal_id.code + "/" + self.period_id.fiscalyear_id.name + "/" + str(
            '0' * (4 - len(str(self.id)))) + str(self.id)
        values = {
            'name': ref,
            'ref': ref,
            'period_id': period_id,
            'journal_id': journal_id,
            'date': self.date,
            'company_id': company.id,
        }
        res = account_pool.create(values)
        account_move_id = res.id
        self.account_move_id = res.id
        if res:

            for line in lines:
                total_line = (line.price_before - line.price_after)
                account_id_bis = line.product_id.categ_id.\
                    devaluation_account_provision_id.id or \
                    company.devaluation_account_provision_id.id

                if total_line > 0:
                    debit = 0
                    credit = total_line * line.quantity
                    account_id = line.product_id.categ_id.\
                        devaluation_account_debit_id.id or \
                        company.devaluation_account_debit_id.id

                else:
                    debit = total_line * line.quantity
                    credit = 0
                    account_id = line.product_id.categ_id.\
                        devaluation_account_credit_id.id or \
                        company.devaluation_account_credit_id.id

                # ipdb.set_trace()
                values = {
                    'name': line.product_id.name + '/' + str('0' * (4 - len(str(line.product_id.id)))) + str(
                        line.product_id.id),
                    'period_id': period_id,
                    'journal_id': journal_id,
                    'date': self.date,
                    'company_id': company.id,
                    'quantity': line.quantity,
                    'product_uom_id': line.product_id.uom_id.id,
                    'product_id': line.product_id.id,
                    'debit': debit,
                    'credit': credit,
                    'move_id': account_move_id,
                    'account_id': account_id,
                    'state': 'draft',
                }
                # ipdb.set_trace()
                res = self.env['account.move.line'].create(values)

                values['debit'] = credit
                values['credit'] = debit
                values['account_id'] = account_id_bis
                res = self.env['account.move.line'].create(values)

            lines.write({'accounted_ok': True})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': 'account.view_move_form',
                'res_id': account_move_id,
                'views': [(False, 'form')],
                }
