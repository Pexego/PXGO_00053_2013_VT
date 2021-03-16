from odoo import models, fields, api


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    amount_insurance = fields.Float("Amount insured")

    @api.multi
    def invoice_validate(self):
        res = super().invoice_validate()
        for invoice in self:
            partner = invoice.partner_id.commercial_partner_id
            if partner.insurance_credit_limit > 0 and \
                    invoice.type == 'out_invoice' and \
                    invoice.payment_term_id != self.env.ref('account.account_payment_term_immediate'):
                # We watch the debt in this moment and then compare it with the credit
                # with this we calculate the amount insured
                credit = partner.insurance_credit_limit
                insured_open_invoices = self.env['account.move.line'].\
                    search([('partner_id', '=', partner.id),
                            ('invoice_id.id', '!=', invoice.id),
                            ('account_id.internal_type', '=', 'receivable'),
                            ('reconciled', '=', False),
                            ('date', '>=', partner.risk_insurance_grant_date)])
                debt = sum(insured_open_invoices.mapped('residual_balance'))
                # Take as maximum the total of the invoice and never less than 0
                if invoice.payment_ids:
                    amt_to_pay = max(invoice.amount_total - sum(invoice.payment_ids.mapped('amount')), 0.0)
                    if amt_to_pay > 0.0:
                        invoice.amount_insurance = max(min(amt_to_pay, max(credit - debt, 0.0)), 0.0)
                else:
                    invoice.amount_insurance = max(min(invoice.amount_total, max(credit - debt, 0.0)), 0.0)
        return res
