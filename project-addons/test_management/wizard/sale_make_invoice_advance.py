# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, _, exceptions, api


class SaleAdvancePaymentInv(models.TransientModel):

    _inherit = 'sale.advance.payment.inv'

    @api.model
    def _get_default_invoice_on_test(self):
        sale_obj = self.env['sale.order']
        orders = sale_obj.browse(self._context.get('active_ids'))
        if all(x.tests for x in orders):
            return True
        elif all(not x.tests for x in orders):
            return False
        else:
            raise exceptions.Warning(
                _('You are trying to invoice normal and test invoice together')
            )

    invoice_on_test = fields.Boolean(default=_get_default_invoice_on_test)

    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(
            self._context.get('active_ids', []))
        res = super().create_invoices()
        if self.invoice_on_test:
            for invoice_id in sale_orders.mapped('invoice_ids')._ids:
                invoice = self.env['account.invoice'].sudo().browse(invoice_id)
                test_company_id = self.env.user.company_id.test_company_id.id
                test_account = self.env["account.account"].sudo().search(
                    [('code', 'like', invoice.account_id.code),
                     ('company_id', '=', test_company_id)], limit=1)
                invoice.write({
                    'company_id': test_company_id,
                    'fiscal_position_id': False,
                    'payment_term_id': False,
                    'payment_mode_id': False,
                    'partner_bank_id': False,
                    'mandate_id': False,
                    'tax_line_ids': [(6, 0, [])],
                    'account_id': test_account.id
                })

                invoice.partner_id.company_id = False
                invoice.commercial_partner_id.company_id = False
                for line in invoice.invoice_line_ids:
                    line.invoice_line_tax_ids = [(6, 0, [])]
                    line.company_id = test_company_id
                    line.move_id = False
                    if line.product_id:
                        line.product_id.company_id = False
                    accounts = self.env["account.account"].sudo().search(
                        [('code', 'like', line.account_id.code),
                         ('company_id', '=', test_company_id)], limit=1)
                    line.account_id = accounts.id
                    line.account_analytic_id = False

                invoice._onchange_invoice_line_ids()
        return res
