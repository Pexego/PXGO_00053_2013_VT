from odoo import models, api


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    def action_invoice_create(self, grouped=False, final=False):
        res = super().action_invoice_create(grouped=grouped, final=final)
        invoices = self.env['account.invoice'].browse(res)
        for invoice in invoices:
            refs = ", ".join(r for r in invoice.sale_order_ids.mapped('client_order_ref'))
            if refs:
                if invoice.comment:
                    invoice.comment += refs
                else:
                    invoice.comment = refs

        return res
