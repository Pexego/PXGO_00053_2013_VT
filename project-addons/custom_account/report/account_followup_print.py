# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.account_followup.report.account_followup_print import report_rappel
from openerp.osv import osv, fields
from collections import defaultdict


def _custom_lines_get_with_partner(self, partner, company_id):
    moveline_obj = self.pool['account.move.line']
    moveline_ids = moveline_obj.search(self.cr, self.uid, [
                        ('partner_id', '=', partner.id),
                        ('account_id.type', '=', 'receivable'),
                        ('reconcile_id', '=', False),
                        ('state', '!=', 'draft'),
                        ('company_id', '=', company_id),
                        '|', ('date_maturity', '=', False), ('date_maturity', '<=', fields.date.context_today(self, self.cr, self.uid)),
                    ])

    # lines_per_currency = {currency: [line data, ...], ...}
    lines_per_currency = defaultdict(list)
    for line in moveline_obj.browse(self.cr, self.uid, moveline_ids):
        currency = line.currency_id or line.company_id.currency_id
        invoice_obj = self.pool['account.invoice']
        if line.stored_invoice_id:
            invoice = invoice_obj.browse(self.cr, self.uid, line.stored_invoice_id[0].id)
            client_order_ref = invoice.invoice_line[0].move_id.procurement_id.sale_line_id.order_id.client_order_ref
            if not client_order_ref:
                client_order_ref = ""
        else:
            client_order_ref = ""

        line_data = {
            'name': line.move_id.name,
            'ref': line.ref,
            'date': line.date,
            'date_maturity': line.date_maturity,
            'balance': line.amount_currency if currency != line.company_id.currency_id else line.debit - line.credit,
            'blocked': line.blocked,
            'currency_id': currency,
            'client_order_ref':client_order_ref,
        }
        lines_per_currency[currency].append(line_data)

    return [{'line': lines, 'currency': currency} for currency, lines in lines_per_currency.items()]

if not hasattr(report_rappel, 'old_lines_get_with_partner'):
    report_rappel.old_lines_get_with_partner = report_rappel._lines_get_with_partner
if not hasattr(report_rappel, '_custom_lines_get_with_partner'):
    report_rappel.custom_lines_get_with_partner = _custom_lines_get_with_partner


def _lines_get_with_partner(self, partner, company_id):
    res = self.custom_lines_get_with_partner(partner, company_id)
    for dct in res:
        dct['line'] = [x for x in dct['line'] if not x['blocked']]
    return [x for x in res if x['line']]

report_rappel._lines_get_with_partner = _lines_get_with_partner
