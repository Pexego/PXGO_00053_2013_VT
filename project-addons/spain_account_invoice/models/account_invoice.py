# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _report_xls_fields(self, cr, uid, invoice_type, context=None):
        datas = ""
        if invoice_type == 'out_invoice':
            datas = [
                'number', 'date_invoice', 'partner_vat', 'partner_name', 'tax_base',
                'tax_amount', 'tax_percent', 'tax_amount_rec', 'tax_amount_ret',
                'amount_total', 'country_name', 'tax_description', 'fiscal_name'
            ]
        elif invoice_type == 'in_invoice':
            datas = [
                'date_invoice', 'number', 'supplier_number', 'partner_vat', 'partner_name', 'tax_base',
                'tax_description', 'tax_amount', 'tax_amount_ret', 'amount_total', 'country_name'
            ]
        elif invoice_type == 'intrastat':
           datas = [

           ]

        return datas

    def _report_xls_template(self, cr, uid, context=None):
        return {}