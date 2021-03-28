from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('payment_term_id', 'date_invoice', 'value_date')
    def _onchange_payment_term_date_invoice(self):
        super()._onchange_payment_term_date_invoice()
        if self.sale_order_ids and len(self.sale_order_ids) == 1:
            if self.sale_order_ids.prepaid_option:
                self.date_due = self.date_invoice
