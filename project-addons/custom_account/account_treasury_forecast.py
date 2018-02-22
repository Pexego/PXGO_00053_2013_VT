# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
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
from openerp import models, fields, tools, api, exceptions, _
import openerp.addons.decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta

PAYMENT_MODE = [('debit_receipt', 'Debit receipt'),
                ('transfer', 'Transfer'),
                ('both', 'Both')]

PERIOD = [('days', 'Days'), ('months', 'Months')]


class AccountTreasuryForecast(models.Model):
    _inherit = "account.treasury.forecast"

    payment_mode_customer = fields.Selection(PAYMENT_MODE, 'Payment mode', default='both')
    account_bank = fields.Many2one('res.partner.bank', 'Account bank',
                                   domain=lambda self: [('partner_id', '=', self.env.user.company_id.partner_id.id)])
    check_old_open_customer = fields.Boolean(string="Old (opened)")
    opened_start_date_customer = fields.Date(string="Start Date")
    payment_mode_supplier = fields.Selection(PAYMENT_MODE, 'Payment mode', default='both')
    check_old_open_supplier = fields.Boolean(string="Old (opened)")
    opened_start_date_supplier = fields.Date(string="Start Date")
    not_bankable_supplier = fields.Boolean(string="Without Bankable Suppliers")
    not_bank_maturity = fields.Boolean(string="Without Bank Maturities",
                                       help="It will be reflected in the treasury analysis")

    @api.one
    @api.constrains('payment_mode_customer', 'check_old_open_customer',
                    'payment_mode_supplier', 'check_old_open_supplier',
                    'opened_start_date_customer', 'opened_start_date_supplier', 'start_date')
    def check_filter(self):
        if not self.payment_mode_customer or not self.payment_mode_supplier:
            raise exceptions.Warning(
                _('Error!:: You must select one option for payment mode fields.'))
        elif self.payment_mode_customer != 'debit_receipt' and self.check_old_open_customer \
                and self.opened_start_date_customer >= self.start_date:
            raise exceptions.Warning(
                _('Error!:: Start date of old opened invoices in customers must be lower '
                  'than the start date specified before.'))
        elif self.payment_mode_supplier != 'debit_receipt' and self.check_old_open_supplier \
                and self.opened_start_date_supplier >= self.start_date:
            raise exceptions.Warning(
                _('Error!:: Start date of old opened invoices in suppliers must be lower '
                  'than the start date specified before.'))

    @api.one
    def calculate_invoices(self):
        invoice_obj = self.env['account.invoice']
        treasury_invoice_obj = self.env['account.treasury.forecast.invoice']
        new_invoice_ids = []
        in_invoice_lst = []
        out_invoice_lst = []

        # CUSTOMER
        search_filter_customer = ['&', ('type', 'in', ['out_invoice', 'out_refund'])]
        if self.payment_mode_customer == 'debit_receipt':
            search_filter_customer.extend([('payment_mode_id.treasury_forecast_type', '=', 'debit_receipt'),
                                           ('state', 'in', ['open', 'paid']),
                                           ('date_due', '>=', self.start_date), ('date_due', '<=', self.end_date)])
        else:
            if self.payment_mode_customer == 'both':
                search_filter_customer.extend(['|',
                                               '&', ('payment_mode_id.treasury_forecast_type', '=', 'debit_receipt'),
                                               '&', ('state', 'in', ['open', 'paid']),
                                               '&', ('date_due', '>=', self.start_date),
                                               ('date_due', '<=', self.end_date)])

            if self.account_bank:
                search_filter_customer.extend(['&', ('payment_mode_id.bank_id', '=', self.account_bank.id)])

            if self.check_old_open_customer:
                start_date = self.opened_start_date_customer
            else:
                start_date = self.start_date

            search_filter_customer.extend(['&', ('payment_mode_id.treasury_forecast_type', '=', 'transfer'),
                                           '&', ('state', '=', 'open'),
                                           '&', ('date_due', '>=', start_date), ('date_due', '<=', self.end_date)])
        invoice_ids = invoice_obj.search(search_filter_customer, order='date_due asc, id asc')
        for invoice_o in invoice_ids:
            values = {
                'invoice_id': invoice_o.id,
                'date_due': invoice_o.date_due,
                'partner_id': invoice_o.partner_id.id,
                'journal_id': invoice_o.journal_id.id,
                'state': invoice_o.state,
                'base_amount': invoice_o.subtotal_wt_rect,
                'tax_amount': -invoice_o.amount_tax if 'refund' in invoice_o.type else invoice_o.amount_tax,
                'total_amount': invoice_o.total_wt_rect,
                'residual_amount': -invoice_o.residual if 'refund' in invoice_o.type else invoice_o.residual,
            }
            new_id = treasury_invoice_obj.create(values)
            new_invoice_ids.append(new_id)
            out_invoice_lst.append(new_id.id)

        # SUPPLIER
        search_filter_supplier = ['&', '&', ('type', 'in', ['in_invoice', 'in_refund']),
                                  ('partner_id.commercial_partner_id', '!=', 148435)]  # Omit AEAT invoices

        if self.payment_mode_supplier == 'debit_receipt':
            search_filter_supplier.extend([('payment_mode_id.treasury_forecast_type', '=', 'debit_receipt'),
                                           ('state', 'in', ['open', 'paid']),
                                           ('date_due', '>=', self.start_date), ('date_due', '<=', self.end_date)])
        else:
            if self.payment_mode_supplier == 'both':
                search_filter_supplier.extend(['|',
                                               '&',
                                               ('payment_mode_id.treasury_forecast_type', '=', 'debit_receipt'),
                                               '&', ('state', 'in', ['open', 'paid']),
                                               '&', ('date_due', '>=', self.start_date),
                                               ('date_due', '<=', self.end_date)])

            if self.check_old_open_supplier:
                start_date = self.opened_start_date_supplier
            else:
                start_date = self.start_date

            if self.not_bankable_supplier:
                id_currency_usd = self.env.ref("base.USD").id
                search_filter_supplier.extend(['&', '|', ('partner_id.property_product_pricelist_purchase.currency_id',
                                                          '!=', id_currency_usd),
                                               ('partner_id.property_account_payable.code', '!=', '40000000')])

            search_filter_supplier.extend(['&', ('payment_mode_id.treasury_forecast_type', '=', 'transfer'),
                                           '&', ('state', '=', 'open'),
                                           '&', ('date_due', '>=', start_date), ('date_due', '<=', self.end_date)])

        invoice_ids = invoice_obj.search(search_filter_supplier, order='date_due asc, id asc')
        for invoice_o in invoice_ids:
            values = {
                'invoice_id': invoice_o.id,
                'date_due': invoice_o.date_due,
                'partner_id': invoice_o.partner_id.id,
                'journal_id': invoice_o.journal_id.id,
                'state': invoice_o.state,
                'base_amount': invoice_o.subtotal_wt_rect,
                'tax_amount': -invoice_o.amount_tax if 'refund' in invoice_o.type else invoice_o.amount_tax,
                'total_amount': invoice_o.total_wt_rect,
                'residual_amount': -invoice_o.residual if 'refund' in invoice_o.type else invoice_o.residual,
            }
            new_id = treasury_invoice_obj.create(values)
            new_invoice_ids.append(new_id)
            in_invoice_lst.append(new_id.id)

        self.write({'out_invoice_ids': [(6, 0, out_invoice_lst)],
                    'in_invoice_ids': [(6, 0, in_invoice_lst)]})

        return new_invoice_ids

    @api.model
    def next_date_period(self, date_origin, period, quantity):
        date = datetime.strptime(date_origin, "%Y-%m-%d")
        if period == 'days':
            date_calculated = (datetime(date.year, date.month, date.day) + relativedelta(days=quantity))
        else:
            date_calculated = (datetime(date.year, date.month, date.day) + relativedelta(months=quantity))
        return date_calculated.strftime('%Y-%m-%d')

    @api.one
    def calculate_line(self):
        new_line_ids = []
        line_obj = self.env['account.treasury.forecast.line']
        temp_line_obj = self.env['account.treasury.forecast.line.template']
        temp_line_lst = temp_line_obj.search([('treasury_template_id', '=', self.template_id.id)])
        for line_o in temp_line_lst:
            date_calculated = line_o.date
            while date_calculated <= self.end_date and not line_o.paid:
                if self.start_date <= date_calculated <= self.end_date:
                    values = {
                        'name': line_o.name,
                        'date': date_calculated,
                        'line_type': line_o.line_type,
                        'partner_id': line_o.partner_id.id,
                        'template_line_id': line_o.id,
                        'amount': line_o.amount,
                        'treasury_id': self.id,
                    }
                    new_line_id = line_obj.create(values)
                    new_line_ids.append(new_line_id)
                date_calculated = self.next_date_period(date_calculated, line_o.period_type, line_o.period_quantity)
        return new_line_ids

    @api.multi
    def write(self, vals):
        if 'check_old_open_customer' in vals and not vals['check_old_open_customer']:
            vals['opened_start_date_customer'] = False
        if 'check_old_open_supplier' in vals and not vals['check_old_open_supplier']:
            vals['opened_start_date_supplier'] = False
        return super(AccountTreasuryForecast, self).write(vals)

    @api.one
    def calc_final_amount(self):
        super(AccountTreasuryForecast, self).calc_final_amount()
        balance = self.final_amount
        for recurring_line in self.recurring_line_ids.search([('paid', '=', True)]):
            balance += recurring_line.amount
        self.final_amount = balance


class BankMaturity(models.Model):
    _name = "bank.maturity"

    bank_account = fields.Many2one("res.partner.bank", string="Bank account",
                                   domain=lambda self: [("partner_id", "=", self.env.user.company_id.partner_id.id)])
    bank_name = fields.Char("Bank", related='bank_account.bank_name', readonly=True)
    date_due = fields.Date(string="Due Date")
    amount = fields.Float(string="Amount", digits_compute=dp.get_precision('Account'))
    paid = fields.Boolean(string="Paid")


class AccountTreasuryForecastLineTemplate(models.Model):
    _inherit = 'account.treasury.forecast.line.template'

    period_quantity = fields.Integer("Quantity")
    period_type = fields.Selection(PERIOD, string="Period")


class AccountTreasuryForecastLine(models.Model):
    _inherit = 'account.treasury.forecast.line'

    paid = fields.Boolean(string="Paid")


class ReportAccountTreasuryForecastAnalysis(models.Model):
    _inherit = 'report.account.treasury.forecast.analysis'
    _order = 'treasury_id asc, date asc, id_ref asc'

    id_ref = fields.Char(string="Id Reference")
    concept = fields.Char(string="Concept")
    partner_name = fields.Char('Partner/Supplier')
    bank_id = fields.Many2one('res.partner.bank', string='Bank Account')
    accumulative_balance = fields.Float(string="Accumulated", digits_compute=dp.get_precision('Account'))

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_account_treasury_forecast_analysis')
        cr.execute("""
            create or replace view report_account_treasury_forecast_analysis
                as (
                    SELECT	    analysis.id, 
                                analysis.treasury_id, 
                                analysis.id_ref, 
                                analysis.date, 
                                analysis.concept, 
                                analysis.partner_name, 
                                analysis.payment_mode_id,
                                pm.bank_id,
                                analysis.credit, 
                                analysis.debit, 
                                analysis.balance, 
                                analysis.type,
                                sum(balance) OVER (PARTITION BY analysis.treasury_id
                                            ORDER BY analysis.treasury_id desc, analysis.date, analysis.id_ref) AS accumulative_balance
                            FROM (
                                select  '0' as id,
                                    0 as id_ref,
                                    'Importe inicial' as concept,
                                    tf.id as treasury_id,
                                    LEAST(tf.start_date, tf.opened_start_date_customer, tf.opened_start_date_supplier) as date,
                                    null as credit,
                                    null as debit,
                                    start_amount as balance,
                                    null as payment_mode_id,
                                    null as type,
                                    null partner_name
                                from    account_treasury_forecast tf 
                                where   tf.start_amount > 0 -- Incluir linea de importe inicial
                                union
                                select
                                    tfl.id || 'l' AS id,
                                    tfl.id as id_ref,
                                    tfl.name as concept,
                                    treasury_id,
                                    tfl.date as date,
                                    CASE WHEN tfl.line_type='receivable' THEN 0.0
                                    ELSE amount
                                    END as credit,
                                    CASE WHEN tfl.line_type='receivable' THEN amount
                                    ELSE 0.0
                                    END as debit,
                                    CASE WHEN tfl.line_type='receivable' THEN amount
                                    ELSE -amount
                                    END as balance,
                                    payment_mode_id,
                                    CASE WHEN tfl.line_type='receivable' THEN 'in'
                                    ELSE 'out'
                                    END as type,
                                    rp.display_name as partner_name
                                from    account_treasury_forecast tf 
                                    inner join account_treasury_forecast_line tfl on tf.id = tfl.treasury_id 
                                                                                        and coalesce(tfl.paid, False) = False
                                    left join res_partner rp ON rp.id = tfl.partner_id
                                union
                                select
                                    tcf.id || 'c' AS id,
                                    tcf.id as id_ref,
                                    tcf.name as concept,
                                    treasury_id,
                                    tcf.date as date,
                                    CASE WHEN tcf.flow_type='in' THEN 0.0
                                    ELSE abs(amount)
                                    END as credit,
                                    CASE WHEN tcf.flow_type='in' THEN amount
                                    ELSE 0.0
                                    END as debit,
                                    amount as balance,
                                    payment_mode_id,
                                    flow_type as type,
                                    null as partner_id
                                from    account_treasury_forecast tf 
                                    inner join account_treasury_forecast_cashflow tcf on tf.id = tcf.treasury_id
                                union
                                select
                                    tfii.id || 'i' AS id,
                                    ai.id as id_ref, 
                                    ai.number as concept,
                                    treasury_id,
                                    tfii.date_due as date,
                                    CASE WHEN ai.type='in_invoice' THEN ABS(tfii.total_amount)
                                    ELSE 0.0
                                    END as credit,
                                    CASE WHEN ai.type='in_invoice' THEN 0.0
                                    ELSE ABS(tfii.total_amount)
                                    END as debit,
                                    -tfii.total_amount as balance,
                                    tfii.payment_mode_id,
                                    CASE WHEN ai.type='in_invoice' THEN 'out'
                                    ELSE 'in'
                                    END as type,
                                    rp.display_name as partner_name
                                    from
                                    account_treasury_forecast tf 
                                    inner join account_treasury_forecast_in_invoice_rel tfiir on tf.id = tfiir.treasury_id 
                                    inner join account_treasury_forecast_invoice tfii on tfii.id = tfiir.in_invoice_id 
                                    inner join account_invoice ai on ai.id = tfii.invoice_id
                                    left join res_partner rp ON rp.id = tfii.partner_id
                                union
                                select
                                    tfio.id || 'o' AS id,
                                    ai.id as id_ref, 
                                    ai.number as concept,
                                    treasury_id,
                                    tfio.date_due as date,
                                    CASE WHEN ai.type='out_invoice' THEN 0.0
                                    ELSE ABS(tfio.total_amount)
                                    END as credit,
                                    CASE WHEN ai.type='out_invoice' THEN ABS(tfio.total_amount)
                                    ELSE 0.0
                                    END as debit,
                                    tfio.total_amount as balance,
                                    tfio.payment_mode_id,
                                    CASE WHEN ai.type='out_invoice' THEN 'in'
                                    ELSE 'out'
                                    END as type,
                                    rp.display_name as partner_name
                                from    account_treasury_forecast tf 
                                    inner join account_treasury_forecast_out_invoice_rel tfior on tf.id = tfior.treasury_id 
                                    inner join account_treasury_forecast_invoice tfio on tfio.id = tfior.out_invoice_id 
                                    inner join account_invoice ai on ai.id = tfio.invoice_id
                                    left join res_partner rp ON rp.id = tfio.partner_id
                                union
                                select  bm.id || 'v' as id,
                                    bm.id as id_ref,
                                    'Vencimiento bancario' as concept,
                                    atf.id as treasury_id,
                                    bm.date_due as date,
                                    null as credit,
                                    null as debit,
                                    -bm.amount as balance,
                                    null as payment_mode_id,
                                    'out' as type,
                                    rpb.bank_name partner_name
                                    from    bank_maturity bm -- Incluir próximos vencimientos
                                    INNER JOIN res_partner_bank rpb ON rpb.id = bm.bank_account
                                    cross join  account_treasury_forecast atf
                                    WHERE   bm.date_due BETWEEN atf.start_date AND atf.end_date
                                            AND coalesce(bm.paid, False) = False AND atf.not_bank_maturity = False    
                            ) analysis
                            LEFT JOIN payment_mode pm ON pm.id = analysis.payment_mode_id
                            ORDER  BY analysis.treasury_id, analysis.date, analysis.id_ref
            )""")


