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

    name = fields.Char('Number', default=lambda self:
    self.env['product.devaluation'].browse(self.env.context.get('active_ids', False))[0].product_id.name
                       )
    account_move_id = fields.Integer("Account ID")
    period_id = fields.Many2one('account.period', 'Period', default=lambda self:
    self.env['account.period'].find(time())[0].id)
    journal_id = fields.Many2one('account.journal', 'Journal', default=lambda self:
    self.env['product.devaluation'].browse(self.env.context.get('active_ids', False))[
        0].product_id.categ_id.devaluation_journal_id
                                 )
    # line_ids = fields.One2many('account.move.line','move_id')
    date = fields.Date("Date", required=True, default=fields.Date.today())
    company_id = fields.Many2one(related='journal_id.company_id', string='Company')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('close', 'Close')], default='draft')

    @api.multi
    def create_dev_account(self):
        # import ipdb

        account_pool = self.env['account.move']
        product_devaluation = self.env['product.devaluation']
        # product_devaluation_lines_wzd = self.env['product.devaluation.account.line.wizard']
        context_pool = self.env.context.get('active_ids', False)

        if self.state == 'draft':
            ref = self.journal_id.code + "/" + self.period_id.fiscalyear_id.name + "/" + str(
                '0' * (4 - len(str(self.id)))) + str(self.id)
            values = {
                'name': ref,
                'ref': ref,
                'period_id': self.period_id.id,
                'journal_id': self.journal_id.id,
                'date': self.date,
                'company_id': self.company_id.id,
            }
            # ipdb.set_trace()
            res = account_pool.create(values)
            account_move_id = res.id
            self.account_move_id = res.id
            if res:
                lines = product_devaluation.search([('id', 'in', context_pool), ('accounted_ok', '=', False)],
                                                   order='product_id, date_dev asc')
                for line in lines:
                    total_line = (line.price_before - line.price_after)
                    account_id_bis = line.product_id.categ_id.devaluation_account_provision_id.id
                    if total_line > 0:
                        debit = 0
                        credit = total_line * line.quantity
                        account_id = line.product_id.categ_id.devaluation_account_debit_id.id

                    else:
                        debit = total_line * line.quantity
                        credit = 0
                        account_id = line.product_id.categ_id.devaluation_account_credit_id.id

                    values = {
                        'name': self.name + '/' + str('0' * (4 - len(str(line.product_id.id)))) + str(
                            line.product_id.id),
                        'period_id': self.period_id.id,
                        'journal_id': self.journal_id.id,
                        'date': self.date,
                        'company_id': self.company_id.id,
                        'quantity': line.quantity,
                        'product_uom_id': line.product_id.uom_id.id,
                        'product_id': line.product_id.id,
                        'debit': debit,
                        'credit': credit,
                        'move_id': self.account_move_id,
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

                # return {'type': 'ir.actions.act_window_close'}

                # return {
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'view_id': 'account.view_move_form',
                    'res_id': account_move_id,
                    'views': [(False, 'form')],

                }

        if self.state == 'open':
            self.state = 'close'
            return {'type': 'ir.actions.act_window_close'}
