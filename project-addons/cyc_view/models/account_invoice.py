from odoo import models, fields, api


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    amount_insurance = fields.Float("Amount insured")
    residual_insurance = fields.Float(compute='_compute_residual_insurance')

    @api.multi
    def invoice_validate(self):
        res = super().invoice_validate()
        for invoice in self:
            if invoice.partner_id.commercial_partner_id.insurance_credit_limit > 0 and \
                    invoice.type == 'out_invoice' and \
                    invoice.payment_term_id != self.env.ref('account.account_payment_term_immediate') and \
                    not invoice.payment_ids:
                available = invoice.partner_id.commercial_partner_id.credit_available
                # Calculate the quantity insured of the invoice and subtract it from the credit still available
                invoice.partner_id.commercial_partner_id.credit_available = max((available - invoice.amount_total), 0.0)
                invoice.amount_insurance = min(invoice.amount_total, available)
            elif invoice.partner_id.commercial_partner_id.insurance_credit_limit > 0 and invoice.type == 'out_refund':
                invoice.amount_insurance = invoice.amount_total
        return res

    @api.multi
    def _compute_residual_insurance(self):
        for invoice in self:
            paid = invoice.amount_total - invoice.residual
            invoice.residual_insurance = max(invoice.amount_insurance-paid, 0.0)

    @api.multi
    def action_invoice_re_open(self):
        res = super().action_invoice_re_open()
        for invoice in self:
            # Subtract again the qty from the available when reopen
            if invoice.amount_insurance and invoice.amount_insurance > 0 and \
                    invoice.partner_id.commercial_partner_id.insurance_credit_limit > 0 and \
                    invoice.type == 'out_invoice' and\
                    invoice.payment_term_id != self.env.ref('account.account_payment_term_immediate'):
                available = invoice.partner_id.commercial_partner_id.credit_available
                invoice.partner_id.commercial_partner_id.credit_available = \
                    max((available - invoice.amount_insurance), 0.0)

        return res


class AccountPayment(models.Model):

    _inherit = "account.payment"

    def action_validate_invoice_payment(self):
        invoice = self.invoice_ids
        if invoice.amount_insurance and invoice.amount_insurance > 0 and \
                invoice.partner_id.commercial_partner_id.insurance_credit_limit > 0 and \
                invoice.type == 'out_invoice' and \
                invoice.payment_term_id != self.env.ref('account.account_payment_term_immediate'):
            if self.amount <= invoice.residual_insurance:
                invoice.partner_id.commercial_partner_id.credit_available += self.amount
            else:
                invoice.partner_id.commercial_partner_id.credit_available += invoice.residual_insurance
        res = super().action_validate_invoice_payment()
        return res
