from odoo import models, fields, api


class StockDeposit(models.Model):
    _inherit = 'stock.deposit'

    amazon_order_id = fields.Many2one("amazon.sale.order")

    @api.multi
    def create_invoice(self, journal_id=None):
        invoice_ids = super(StockDeposit, self).create_invoice(journal_id)
        if invoice_ids and self.mapped('amazon_order_id'):
            invoices = self.env['account.invoice'].browse(invoice_ids)
            for invoice in invoices:
                deposit = self.filtered(lambda d:d.invoice_id.id==invoice.id)
                if deposit[0].amazon_order_id:
                    invoice.write({'name': deposit[0].amazon_order_id.name,'amazon_order':deposit[0].amazon_order_id.id})
        return invoice_ids