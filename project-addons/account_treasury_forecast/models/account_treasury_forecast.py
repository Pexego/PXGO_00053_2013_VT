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
from datetime import datetime
from dateutil.relativedelta import relativedelta


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
            balance = treasury.start_amount
            for out_invoice in treasury.out_invoice_ids:
                balance += out_invoice.total_amount
            for in_invoice in treasury.in_invoice_ids:
                balance -= in_invoice.total_amount
            for recurring_line in treasury.recurring_line_ids.search([('paid', '=', False)]):
                balance -= recurring_line.amount
            for variable_line in treasury.variable_line_ids:
                balance -= variable_line.amount
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
    payment_mode_customer_m2m = fields.Many2many(
        'account.payment.mode',
        'treasury_forecast_customer_payment_mode_rel',
        string='Payment mode'
    )
    account_bank = fields.Many2one('res.partner.bank', 'Account bank',
                                   domain=lambda self: [('partner_id', '=', self.env.user.company_id.partner_id.id)])
    check_old_open_customer = fields.Boolean(string="Old (opened)")
    opened_start_date_customer = fields.Date(string="Start Date")
    payment_mode_supplier_m2m = fields.Many2many(
        'account.payment.mode',
        'treasury_forecast_supplier_payment_mode_rel',
        string='Payment mode'
    )
    has_transfer_payments_customer = fields.Boolean(
        string='Has transfer payments', compute='_get_has_transfer_payments'
    )
    has_transfer_payments_supplier = fields.Boolean(
        string='Has transfer payments', compute='_get_has_transfer_payments'
    )
    check_old_open_supplier = fields.Boolean(string="Old (opened)")
    opened_start_date_supplier = fields.Date(string="Start Date")
    not_bankable_supplier = fields.Boolean(string="Without Bankable Suppliers")

    @api.depends('payment_mode_customer_m2m', 'payment_mode_supplier_m2m')
    def _get_has_transfer_payments(self):
        """
        Calculates if the object has any transfer payment in supplier and if there
        is any transfer payment in customer
        """
        for each_record in self:
            customer_treasury_forecast_types = each_record.payment_mode_customer_m2m.mapped(
                'treasury_forecast_type'
            )
            supplier_treasury_forecast_types = each_record.payment_mode_supplier_m2m.mapped(
                'treasury_forecast_type'
            )
            each_record.has_transfer_payments_customer = 'transfer' in customer_treasury_forecast_types
            each_record.has_transfer_payments_supplier = 'transfer' in supplier_treasury_forecast_types

    @api.multi
    @api.constrains('end_date', 'start_date')
    def check_date(self):
        for record in self:
            if record.start_date > record.end_date:
                raise exceptions.Warning(_('Error!:: End date is lower than start date.'))

    @api.one
    @api.constrains('payment_mode_customer_m2m', 'check_old_open_customer_m2m',
                    'payment_mode_supplier', 'check_old_open_supplier',
                    'opened_start_date_customer', 'opened_start_date_supplier', 'start_date')
    def check_filter(self):
        if not self.payment_mode_customer_m2m or not self.payment_mode_supplier_m2m:
            raise exceptions.Warning(
                _('Error!:: You must select one option for payment mode fields.'))
        elif ('debit_receipt' not in self.payment_mode_customer_m2m.mapped('treasury_forecast_type')
              and self.check_old_open_customer
              and self.opened_start_date_customer >= self.start_date):
            raise exceptions.Warning(
                _('Error!:: Start date of old opened invoices in customers must be lower '
                  'than the start date specified before.'))
        elif ('debit_receipt' not in self.payment_mode_supplier_m2m.mapped('treasury_forecast_type')
              and self.check_old_open_supplier
              and self.opened_start_date_supplier >= self.start_date):
            raise exceptions.Warning(
                _('Error!:: Start date of old opened invoices in suppliers must be lower '
                  'than the start date specified before.'))

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
        for record in self:
            out_invoice_lst = record._get_customer_invoices()
            in_invoice_lst = record._get_supplier_invoices()
            record.write({'out_invoice_ids': [(6, 0, out_invoice_lst)],
                          'in_invoice_ids': [(6, 0, in_invoice_lst)]})
        return

    def _get_customer_invoices(self):
        """
        Creates invoices to assign in customer page

        Returns:
        -------
            List[account.invoice]
        """
        invoices = []
        invoice_obj = self.env['account.invoice']
        treasury_invoice_obj = self.env['account.treasury.forecast.invoice']
        domain = self._get_customer_invoices_domain()

        invoice_ids = invoice_obj.search(domain, order='date_due asc, id asc')
        for invoice_o in invoice_ids:
            values = {
                'invoice_id': invoice_o.id,
                'date_due': invoice_o.date_due,
                'partner_id': invoice_o.partner_id.id,
                'journal_id': invoice_o.journal_id.id,
                'state': invoice_o.state,
                'base_amount': invoice_o.amount_untaxed_signed,
                'total_amount': invoice_o.amount_total_signed,
                'tax_amount': -invoice_o.amount_tax if 'refund' in invoice_o.type else invoice_o.amount_tax,
                'residual_amount': -invoice_o.residual if 'refund' in invoice_o.type else invoice_o.residual,
            }
            new_id = treasury_invoice_obj.create(values)
            invoices.append(new_id.id)
        return invoices

    def _get_supplier_invoices(self):
        """
        Creates invoices to assign in supplier page

        Returns:
        -------
            List[account.invoice]
        """
        invoices = []
        invoice_obj = self.env['account.invoice']
        treasury_invoice_obj = self.env['account.treasury.forecast.invoice']
        domain = self._get_supplier_invoices_domain()

        invoice_ids = invoice_obj.search(domain, order='date_due asc, id asc')
        for invoice_o in invoice_ids:
            values = {
                'invoice_id': invoice_o.id,
                'date_due': invoice_o.date_due,
                'partner_id': invoice_o.partner_id.id,
                'journal_id': invoice_o.journal_id.id,
                'state': invoice_o.state,
                # TODO -> Pendiente migrar "custom_account"
                # 'base_amount': invoice_o.subtotal_wt_rect,
                # 'total_amount': invoice_o.total_wt_rect,
                'tax_amount': -invoice_o.amount_tax if 'refund' in invoice_o.type else invoice_o.amount_tax,
                'residual_amount': -invoice_o.residual if 'refund' in invoice_o.type else invoice_o.residual,
            }
            new_id = treasury_invoice_obj.create(values)
            invoices.append(new_id.id)
        return invoices

    def _get_customer_invoices_domain(self):
        """
        Creates domain to obtain invoices for customer page

        Returns:
        -------
            List[Any]
        """
        domain = ['&', ('type', 'in', ['out_invoice', 'out_refund'])]
        treasury_forecast_types = self.payment_mode_customer_m2m.mapped('treasury_forecast_type')
        debit_payment_mode_customer = self.payment_mode_customer_m2m.filtered(
            lambda p: p.treasury_forecast_type == 'debit_receipt'
        )
        transfer_payment_mode_customer = self.payment_mode_customer_m2m.filtered(
            lambda p: p.treasury_forecast_type == 'transfer'
        )
        if 'debit_receipt' in treasury_forecast_types:
            if 'transfer' in treasury_forecast_types:
                # only needed when we have both types of forecast
                domain.append('|')
            domain.extend(['&', '&', '&',
                           ('payment_mode_id', 'in', debit_payment_mode_customer.ids),
                           ('state', 'in', ['open', 'paid']),
                           ('date_due', '>=', self.start_date), ('date_due', '<=', self.end_date)])
        if 'transfer' in treasury_forecast_types:
            if self.account_bank:
                domain.extend(['&', ('payment_mode_id.fixed_journal_id.bank_account_id',
                                     '=', self.account_bank.id)])
            if self.check_old_open_customer:
                start_date = self.opened_start_date_customer
            else:
                start_date = self.start_date
            domain.extend(['&', ('payment_mode_id', 'in', transfer_payment_mode_customer.ids),
                           '&', ('state', '=', 'open'),
                           '&', ('date_due', '>=', start_date), ('date_due', '<=', self.end_date)])
        return domain

    def _get_supplier_invoices_domain(self):
        """
        Creates domain to obtain invoices for supplier page

        Returns:
        -------
            List[Any]
        """
        domain = ['&', '&', ('type', 'in', ['in_invoice', 'in_refund']),
                  ('partner_id.commercial_partner_id', '!=', 148435)]  # Omit AEAT invoices
        treasury_forecast_types = self.payment_mode_supplier_m2m.mapped('treasury_forecast_type')
        debit_payment_mode_supplier = self.payment_mode_supplier_m2m.filtered(
            lambda p: p.treasury_forecast_type == 'debit_receipt'
        )
        transfer_payment_mode_supplier = self.payment_mode_supplier_m2m.filtered(
            lambda p: p.treasury_forecast_type == 'transfer'
        )
        if 'debit_receipt' in treasury_forecast_types:
            if 'transfer' in treasury_forecast_types:
                # only needed when we have both types of forecast
                domain.append('|')
            domain.extend(['&', '&', '&', ('payment_mode_id', 'in', debit_payment_mode_supplier.ids),
                           ('state', 'in', ['open', 'paid']),
                           ('date_due', '>=', self.start_date), ('date_due', '<=', self.end_date)])
        if 'transfer' in treasury_forecast_types:
            if self.not_bankable_supplier:
                id_currency_usd = self.env.ref("base.USD").id
                domain.extend(['&', '|',
                               ('partner_id.property_purchase_currency_id', '!=', id_currency_usd),
                               ('partner_id.property_account_payable_id.code', '!=', '40000000')])
            if self.check_old_open_supplier:
                start_date = self.opened_start_date_supplier
            else:
                start_date = self.start_date
            domain.extend(['&', ('payment_mode_id', 'in', transfer_payment_mode_supplier.ids),
                           '&', ('state', '=', 'open'),
                           '&', ('date_due', '>=', start_date), ('date_due', '<=', self.end_date)])
        return domain

    @api.model
    def next_date_period(self, date_origin, period, quantity):
        date = datetime.strptime(date_origin, '%Y-%m-%d')
        if period == 'days':
            date_calculated = (datetime(date.year, date.month, date.day) + relativedelta(days=quantity))
        else:
            date_calculated = (datetime(date.year, date.month, date.day) + relativedelta(months=quantity))
        return date_calculated.strftime('%Y-%m-%d')

    @api.multi
    def calculate_line(self):
        line_obj = self.env['account.treasury.forecast.line']
        temp_line_obj = self.env['account.treasury.forecast.line.template']
        for record in self:
            new_line_ids = []
            temp_line_lst = temp_line_obj.search([('treasury_template_id', '=', record.template_id.id)])
            for line_o in temp_line_lst:
                if line_o.period_quantity and not line_o.paid:
                    date_calculated = line_o.date
                    if date_calculated:
                        while date_calculated <= record.end_date:
                            if record.start_date <= date_calculated <= record.end_date:
                                values = {
                                    'name': line_o.name,
                                    'date': date_calculated,
                                    'line_type': line_o.line_type,
                                    'partner_id': line_o.partner_id.id,
                                    'template_line_id': line_o.id,
                                    'amount': line_o.amount,
                                    'treasury_id': record.id,
                                }
                                new_line_id = line_obj.create(values)
                                new_line_ids.append(new_line_id)
                            date_calculated = record.next_date_period(date_calculated,
                                                                      line_o.period_type,
                                                                      line_o.period_quantity)
        return new_line_ids

    @api.multi
    def write(self, vals):
        if 'check_old_open_customer' in vals and not vals['check_old_open_customer']:
            vals['opened_start_date_customer'] = False
        if 'check_old_open_supplier' in vals and not vals['check_old_open_supplier']:
            vals['opened_start_date_supplier'] = False
        return super(AccountTreasuryForecast, self).write(vals)


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
    paid = fields.Boolean(string="Paid")
