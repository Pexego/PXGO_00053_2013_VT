# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _report_xls_fields(self, cr, uid, context=None):
        return [
            'number', 'date_invoice', 'partner_vat', 'partner_name', 'tax_base',
            'tax_amount', 'tax_percent', 'tax_amount_rec', 'tax_amount_ret',
            'amount_total', 'country_name', 'tax_description', 'fiscal_name'
        ]

    def _report_xls_template(self, cr, uid, context=None):
        return {}pa 