from odoo import fields, models, api


class PurchaseBatchInvoicing(models.TransientModel):
    _inherit = "purchase.batch_invoicing"

    invoice_ref = fields.Char("Invoice Reference", default=lambda self: self._get_reference_inv())

    @api.model
    def _get_reference_inv(self):
        purchases = self.env["purchase.order"].search(self._purchase_order_domain(self.env.context["active_ids"]))
        reference = ""
        for purchase in purchases:
            if purchase.mapped('container_ids'):
                reference += ' - '.join(purchase.mapped('container_ids.name'))
        return reference

    @api.multi
    def action_batch_invoice(self):
        res = {}
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
                    res = super(PurchaseBatchInvoicing,
                                 self.with_context({'default_journal_id': default_journal_id.id})).action_batch_invoice()
        if not res:
            res = super(PurchaseBatchInvoicing, self).action_batch_invoice()

        if self.invoice_ref:
            purchases = self.purchase_order_ids
            invoices = purchases.mapped('invoice_ids')
            invoice_ids = res['domain'][0][2]
            for invoice in invoices.filtered(lambda i: i.id in invoice_ids):
                invoice.reference = self.invoice_ref
        else:
            purchases = self.purchase_order_ids
            invoices = purchases.mapped('invoice_ids')
            invoice_ids = res['domain'][0][2]

            for invoice in invoices.filtered(lambda i: i.id in invoice_ids):
                invoice.reference = False
                purchases_inv = self.env['purchase.order'].search([('name', 'in', invoice.origin.split(', '))])
                if purchases_inv and purchases_inv.mapped('container_ids'):
                    invoice.reference = ' - '.join(purchases_inv.mapped('container_ids.name'))
        return res
