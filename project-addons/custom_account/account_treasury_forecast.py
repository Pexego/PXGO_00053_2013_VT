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
from openerp import models, fields, api, exceptions, _


PAYMENT_MODE = [('debit_receipt', 'Debit receipt'),
                ('transfer', 'Transfer'),
                ('both', 'Both')]


class AccountTreasuryForecast(models.Model):
    _inherit = "account.treasury.forecast"

    payment_mode_customer = fields.Selection(PAYMENT_MODE, 'Payment mode', default='both')
    account_bank = fields.Many2one('res.partner.bank', 'Account bank',
                                   domain=lambda self: [('partner_id', '=', self.env.user.company_id.id)])
    check_old_open_customer = fields.Boolean(string="Old (opened)")
    opened_start_date_customer = fields.Date(string="Start Date")
    payment_mode_supplier = fields.Selection(PAYMENT_MODE, 'Payment mode', default='both')
    check_old_open_supplier = fields.Boolean(string="Old (opened)")
    opened_start_date_supplier = fields.Date(string="Start Date")

    @api.one
    @api.constrains('payment_mode_customer', 'check_old_open_customer',
                    'payment_mode_supplier', 'check_old_open_supplier')
    def check_filter(self):
        if not self.payment_mode_customer or not self.payment_mode_supplier:
            raise exceptions.Warning(
                _('Error!:: You must select one option for payment mode fields.'))
        elif self.payment_mode_customer != 'debit_receipt':
            if self.check_old_open_customer:
                if not self.opened_start_date_customer:
                    raise exceptions.Warning(
                        _('Error!:: You must select start date for old opened invoices in customers.'))
                else:
                    if self.opened_start_date_customer >= self.start_date:
                        raise exceptions.Warning(
                            _('Error!:: Start date of old opened invoices in customers must be lower '
                              'than the start date specified before.'))
        elif self.payment_mode_supplier != 'debit_receipt':
            if self.check_old_open_supplier:
                if not self.opened_start_date_supplier:
                    raise exceptions.Warning(
                        _('Error!:: You must select start date for old opened invoices in suppliers.'))
                else:
                    if self.opened_start_date_supplier >= self.start_date:
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
        invoice_ids = invoice_obj.search(search_filter_customer)
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
            out_invoice_lst.append(new_id.id)

        # SUPPLIER
        search_filter_supplier = ['&', ('type', 'in', ['in_invoice', 'in_refund'])]
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

            search_filter_supplier.extend(['&', ('payment_mode_id.treasury_forecast_type', '=', 'transfer'),
                                           '&', ('state', '=', 'open'),
                                           '&', ('date_due', '>=', start_date), ('date_due', '<=', self.end_date)])
        invoice_ids = invoice_obj.search(search_filter_supplier)
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
            in_invoice_lst.append(new_id.id)

        self.write({'out_invoice_ids': [(6, 0, out_invoice_lst)],
                    'in_invoice_ids': [(6, 0, in_invoice_lst)]})

        return new_invoice_ids


