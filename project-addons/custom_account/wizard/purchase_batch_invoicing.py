from odoo import fields, models, api


class PurchaseBatchInvoicing(models.TransientModel):
    _inherit = "purchase.batch_invoicing"

    @api.multi
    def action_batch_invoice(self):
        if self.purchase_order_ids:
            purchase = self.purchase_order_ids[0]
            if purchase:
                journal_domain = [
                    ('type', '=', 'purchase'),
                    ('company_id', '=', purchase.company_id.id),
                    ('currency_id', '=', purchase.currency_id.id),
                ]
                default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
                if default_journal_id:
                    return super(PurchaseBatchInvoicing,
                                 self.with_context({'default_journal_id': default_journal_id.id})).action_batch_invoice()
        return super(PurchaseBatchInvoicing, self).action_batch_invoice()
