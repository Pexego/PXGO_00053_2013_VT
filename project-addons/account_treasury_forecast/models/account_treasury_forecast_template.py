##############################################################################
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _


class AccountTreasuryForecastTemplate(models.Model):
    _name = 'account.treasury.forecast.template'
    _description = 'Treasury Forecast Template'

    name = fields.Char(string="Description", required=True)
    recurring_line_ids = fields.One2many(
        "account.treasury.forecast.line.template", "treasury_template_id",
        string="Recurring Line", domain=[('line_type', '=', 'recurring')])
    variable_line_ids = fields.One2many(
        "account.treasury.forecast.line.template", "treasury_template_id",
        string="Variable Line", domain=[('line_type', '=', 'variable')])


class AccountTreasuryForecastLineTemplate(models.Model):
    _name = 'account.treasury.forecast.line.template'
    _description = 'Treasury Forecast Line Template'

    name = fields.Char(string="Description", required=True)
    date = fields.Date(string="Date")
    line_type = fields.Selection([('recurring', 'Recurring'),
                                  ('variable', 'Variable')],
                                 string="Treasury Line Type")
    partner_id = fields.Many2one('res.partner', string="Partner")
    journal_id = fields.Many2one('account.journal', string="Journal",
                                 domain=[("type", "=", "purchase")])
    invoice_id = fields.Many2one('account.invoice', string="Invoice",
                                 domain=[("type", "=", "in_invoice")])
    amount = fields.Float(string="Amount",
                          digits=dp.get_precision('Account'))
    paid = fields.Boolean(string="Invoiced/Paid")
    treasury_template_id = fields.Many2one(
        'account.treasury.forecast.template', string="Treasury Template")

    @api.multi
    @api.onchange('invoice_id')
    def onchange_invoice(self):
        for record in self:
            if record.invoice_id:
                record.journal_id = record.invoice_id.journal_id.id
                record.partner_id = record.invoice_id.partner_id.id
                record.amount = record.invoice_id.amount_total
                record.date = record.invoice_id.date_invoice
                record.paid = True

    @api.multi
    def create_invoice(self):
        wiz_obj = self.env['wiz.create.invoice']
        inv_wiz_values = {'partner_id': self.partner_id.id,
                          'journal_id': self.journal_id.id,
                          'description': self.name,
                          'amount': self.amount,
                          'line_id': self.id
                          }
        wiz_id = wiz_obj.create(inv_wiz_values)
        return {'name': _('Create Invoice'),
                'type': 'ir.actions.act_window',
                'res_model': 'wiz.create.invoice',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': wiz_id.id,
                'target': 'new',
                }
