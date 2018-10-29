# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import api, fields, models


class XlsInvoiceReportWizard(models.TransientModel):
    _name = 'xls.invoice.report.wizard'

    _defaults = {
        'invoice_type': 'out_invoice',
    }

    INVOICE_TYPES = [
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Supplier Invoice')
    ]

    COUNTRY_GROUP_TYPE = [
        ('1', 'Europe'),
        ('2', 'Non Europe')
    ]
    invoice_type = fields.Selection(INVOICE_TYPES, 'Invoice Type', required=True)
    country_group = fields.Selection(COUNTRY_GROUP_TYPE, 'Country Group')
    period_ids = fields.Many2many('account.period', string='Periods', required=True)
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'account.invoice'))

    @api.multi
    def xls_export(self):
        self.ensure_one()
        datas = {
            'model': 'xls.invoice.report.wizard',
            'invoice_type': self.invoice_type,
            'country_group': self.country_group,
            'company_id': self.company_id.id,
            'period_ids': map(lambda p: p.id, self.period_ids),
            'ids': [self.id]
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.invoice.export.xls',
            'datas': datas
        }
