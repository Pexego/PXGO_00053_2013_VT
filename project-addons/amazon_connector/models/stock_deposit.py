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
                deposit = self.filtered(lambda d: d.invoice_id.id == invoice.id)
                if deposit[0].amazon_order_id:
                    amazon_order = deposit[0].amazon_order_id
                    rate = amazon_order.currency_id.with_context(date=amazon_order.purchase_date)._get_conversion_rate(
                        invoice.journal_id.company_id.currency_id,
                        amazon_order.currency_id)
                    invoice.write(
                        {'name': amazon_order.name, 'amazon_order': amazon_order.id, 'amazon_invoice': amazon_order.amazon_invoice_name})
                    for line in invoice.invoice_line_ids:
                        o_line = amazon_order.order_line.filtered(lambda l: l.product_id == line.product_id)[0]
                        line.write(
                            {'invoice_line_tax_ids': [(6, 0, o_line.tax_id.ids)], 'price_unit': o_line.price_unit / rate,
                             'discount': 0})
                    invoice._onchange_invoice_line_ids()
        return invoice_ids
