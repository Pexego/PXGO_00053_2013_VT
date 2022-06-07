from odoo import models, api


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super().action_invoice_create(grouped=grouped, final=final)
        invoices = self.env['account.invoice'].browse(res)
        for invoice in invoices:
            if invoice.sale_order_ids.mapped('client_order_ref'):
                refs = ", ".join(r for r in invoice.sale_order_ids.filtered(lambda p: p.client_order_ref is not False).mapped('client_order_ref'))
                if refs:
                    if invoice.comment:
                        invoice.comment += refs
                    else:
                        invoice.comment = refs

        return res
