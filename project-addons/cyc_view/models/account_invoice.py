from odoo import models, fields, api


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    amount_insurance = fields.Float("Amount insured")

    @api.multi
    def invoice_validate(self):
        res = super().invoice_validate()
        for invoice in self:
            if invoice.partner_id.commercial_partner_id.insurance_credit_limit > 0 and \
                    invoice.type == 'out_invoice' and \
                    invoice.payment_term_id != self.env.ref('account.account_payment_term_immediate') and \
                    not invoice.payment_ids:
                # We watch the debt in this moment and then compare it with the credit
                # with this we calculate the amount insured
                credit = invoice.partner_id.commercial_partner_id.insurance_credit_limit
                insured_open_invoices = self.env['account.move.line'].\
                    search([('partner_id', '=', invoice.partner_id.commercial_partner_id.id),
                            ('account_id.internal_type', '=', 'receivable'),
                            ('reconciled', '=', False),
                            '|', ('invoice_id.amount_insurance', '!=', False), ('balance', '<', 0)])
                debt = sum(insured_open_invoices.mapped('residual_balance'))
                # Take as maximum the total of the invoice and never less than 0
                invoice.amount_insurance = max(min(invoice.amount_total, max(credit - debt, 0.0)), 0.0)
        return res
