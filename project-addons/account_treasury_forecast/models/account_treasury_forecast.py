##############################################################################
#
#    Avanzosc - Avanced Open Source Consulting
#    Copyright (C) 2010 - 2011 Avanzosc <http://www.avanzosc.com>
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
from odoo import models, fields, api, exceptions, _


class AccountTreasuryForecastInvoice(models.Model):
    _name = 'account.treasury.forecast.invoice'
    _description = 'Treasury Forecast Invoice'

    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    date_due = fields.Date(string="Due Date")
    partner_id = fields.Many2one('res.partner', string="Partner")
    journal_id = fields.Many2one('account.journal', string="Journal")
    state = fields.Selection([('draft', 'Draft'), ('proforma', 'Pro-forma'),
                              ('proforma2', 'Pro-forma'), ('open', 'Opened'),
                              ('paid', 'Paid'), ('cancel', 'Canceled')],
                             string="State")
    base_amount = fields.Float(string="Base Amount",
                               digits=dp.get_precision('Account'))
    tax_amount = fields.Float(string="Tax Amount",
                              digits=dp.get_precision('Account'))
    total_amount = fields.Float(string="Total Amount",
                                digits=dp.get_precision('Account'))
    residual_amount = fields.Float(string="Residual Amount",
                                   digits=dp.get_precision('Account'))


class AccountTreasuryForecast(models.Model):
    _name = 'account.treasury.forecast'
    _description = 'Treasury Forecast'

    @api.multi
    def calc_final_amount(self):
        for treasury in self:
            balance = 0
            for out_invoice in treasury.out_invoice_ids:
                balance += out_invoice.total_amount
            for in_invoice in treasury.in_invoice_ids:
                balance -= in_invoice.total_amount
            for recurring_line in treasury.recurring_line_ids:
                balance -= recurring_line.amount
            for variable_line in treasury.variable_line_ids:
                balance -= variable_line.amount
            balance += treasury.start_amount
            treasury.final_amount = balance

    name = fields.Char(string="Description", required=True)
    template_id = fields.Many2one('account.treasury.forecast.template',
                                  string="Template", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    start_amount = fields.Float(string="Start Amount",
                                digits=dp.get_precision('Account'))
    final_amount = fields.Float(string="Final Amount",
                                compute="calc_final_amount",
                                digits=dp.get_precision('Account'))
    check_draft = fields.Boolean(string="Draft", default=1)
    check_proforma = fields.Boolean(string="Proforma", default=1)
    check_open = fields.Boolean(string="Opened", default=1)
    out_invoice_ids = fields.Many2many(
        comodel_name='account.treasury.forecast.invoice',
        relation="account_treasury_forecast_out_invoice_rel",
        column1='treasury_id', column2="out_invoice_id",
        string="Out Invoices")
    in_invoice_ids = fields.Many2many(
        comodel_name='account.treasury.forecast.invoice',
        relation="account_treasury_forecast_in_invoice_rel",
        column1='treasury_id', column2="in_invoice_id",
        string="In Invoices")
    recurring_line_ids = fields.One2many(
        'account.treasury.forecast.line', 'treasury_id',
        string="Recurring Lines", domain=[('line_type', '=', 'recurring')])
    variable_line_ids = fields.One2many(
        'account.treasury.forecast.line', 'treasury_id',
        string="Variable Lines", domain=[('line_type', '=', 'variable')])

    @api.multi
    @api.constrains('end_date', 'start_date')
    def check_date(self):
        for record in self:
            if record.start_date > record.end_date:
                raise exceptions.Warning(_('Error!:: End date is lower than start date.'))

    @api.multi
    @api.constrains('check_draft', 'check_proforma', 'check_open')
    def check_filter(self):
        for record in self:
            if not record.check_draft and not record.check_proforma and not record.check_open:
                raise exceptions.Warning(_('Error!:: There is no any filter checked.'))

    @api.multi
    def restart(self):
        for record in self:
            record.out_invoice_ids.unlink()
            record.in_invoice_ids.unlink()
            record.recurring_line_ids.unlink()
            record.variable_line_ids.unlink()
            return True

    @api.multi
    def button_calculate(self):
        for record in self:
            record.restart()
            record.calculate_invoices()
            record.calculate_line()
        return True

    @api.multi
    def calculate_invoices(self):
        invoice_obj = self.env['account.invoice']
        treasury_invoice_obj = self.env['account.treasury.forecast.invoice']
        for record in self:
            new_invoice_ids = []
            in_invoice_lst = []
            out_invoice_lst = []
            state = []
            if record.check_draft:
                state.append("draft")
            if record.check_proforma:
                state.append("proforma")
            if record.check_open:
                state.append("open")
            invoice_ids = invoice_obj.search([('date_due', '>', record.start_date),
                                              ('date_due', '<', record.end_date),
                                              ('state', 'in', tuple(state))])
            for invoice_o in invoice_ids:
                values = {
                    'invoice_id': invoice_o.id,
                    'date_due': invoice_o.date_due,
                    'partner_id': invoice_o.partner_id.id,
                    'journal_id': invoice_o.journal_id.id,
                    'state': invoice_o.state,
                    'base_amount': invoice_o.amount_untaxed,
                    'tax_amount': invoice_o.amount_tax,
                    'total_amount': invoice_o.amount_total,
                    'residual_amount': invoice_o.residual,
                }
                new_id = treasury_invoice_obj.create(values)
                new_invoice_ids.append(new_id)
                if invoice_o.type in ("out_invoice", "out_refund"):
                    out_invoice_lst.append(new_id.id)
                elif invoice_o.type in ("in_invoice", "in_refund"):
                    in_invoice_lst.append(new_id.id)
            record.write({'out_invoice_ids': [(6, 0, out_invoice_lst)],
                          'in_invoice_ids': [(6, 0, in_invoice_lst)]})
        return new_invoice_ids

    @api.multi
    def calculate_line(self):
        line_obj = self.env['account.treasury.forecast.line']
        temp_line_obj = self.env['account.treasury.forecast.line.template']
        for record in self:
            new_line_ids = []
            temp_line_lst = temp_line_obj.search([('treasury_template_id', '=', record.template_id.id)])
            for line_o in temp_line_lst:
                if not line_o.date or record.start_date < line_o.date < record.end_date and not line_o.paid:
                    values = {
                        'name': line_o.name,
                        'date': line_o.date,
                        'line_type': line_o.line_type,
                        'partner_id': line_o.partner_id.id,
                        'template_line_id': line_o.id,
                        'amount': line_o.amount,
                        'treasury_id': record.id,
                    }
                    new_line_id = line_obj.create(values)
                    new_line_ids.append(new_line_id)
        return new_line_ids


class AccountTreasuryForecastLine(models.Model):
    _name = 'account.treasury.forecast.line'
    _description = 'Treasury Forecast Line'

    name = fields.Char(string="Description")
    line_type = fields.Selection([('recurring', 'Recurring'),
                                  ('variable', 'Variable')],
                                 string="Treasury Line Type")
    date = fields.Date(string="Date")
    partner_id = fields.Many2one('res.partner', string="Partner")
    amount = fields.Float(string="Amount",
                          digits=dp.get_precision('Account'))
    template_line_id = fields.Many2one('account.treasury.forecast.line.template', string="Template Line")
    treasury_id = fields.Many2one('account.treasury.forecast', string="Treasury")
