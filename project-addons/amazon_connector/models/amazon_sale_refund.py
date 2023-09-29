from odoo import models, fields, api, _
from datetime import datetime


class AmazonSaleRefund(models.Model):
    _name = 'amazon.sale.refund'

    _rec_name = "amazon_order_name"

    amazon_order_id = fields.Many2one("amazon.sale.order")
    state = fields.Selection([
        ('error', 'Error'),
        ('refund_created', 'Refund created')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='error')

    product_id = fields.Many2one("product.product")
    asin_code = fields.Char()
    amazon_order_name = fields.Char()
    product_qty = fields.Float()
    price_unit = fields.Float()
    refund_id = fields.Many2one("account.invoice")
    purchase_date = fields.Date("Purchase Date", related="amazon_order_id.purchase_date")
    refund_date = fields.Date("Shipment Date")
    amazon_refund_name = fields.Char("Amazon Invoice")
    shipment_id = fields.Char("Shipment")
    error_message = fields.Char()
    marketplace_id = fields.Many2one("amazon.marketplace", related="amazon_order_id.sales_channel")

    def create_refunds(self, input_file, max_commit_len, only_read=False):
        refunds_len = len(input_file.index)
        for number, row in input_file.iterrows():
            order_name = row["Order ID"]
            shipment_id = row["Shipment ID"]
            exist_refund = self.env['amazon.sale.refund'].search([('shipment_id', '=', shipment_id)])
            quantity = row['Quantity']
            if exist_refund or quantity <= 0:
                continue
            order_id = self.env['amazon.sale.order'].search([('name', '=', order_name)])
            asin_code = row["ASIN"]
            refund_id = self.env['amazon.sale.refund'].create({
                'asin_code': asin_code,
                'product_qty': quantity,
                'amazon_order_id': order_id.id or False,
                'amazon_order_name': order_name,
                'shipment_id': row['Shipment ID'],
                'refund_date': row['Shipment Date'],
                'amazon_refund_name': row['VAT Invoice Number'],
                'product_id': self.env['product.product'].search([('asin_code', '=', asin_code)]).id or False})
            error_message = refund_id.check_errors()
            if error_message:
                refund_id.error_message = error_message
                continue
            if not only_read:
                refund_id.process_refund()
            if (number >= max_commit_len and number % max_commit_len == 0) or number == refunds_len:
                self.env.cr.commit()

    def check_errors(self):
        error_message = ""
        if not self.amazon_order_id:
            error_message += _("There is no order for this refund")
        elif self.amazon_order_id.state != 'invoice_open':
            error_message += _("There order has not been invoiced yet")
        if not self.product_id:
            error_message += _("There is no product with this ASIN Code: %s") % self.asin_code
        return error_message

    @api.multi
    def process_refund(self):
        for refund in self:
            lines = refund.amazon_order_id.invoice_deposits.filtered(
                lambda i: i.state != 'cancel' and i.type != 'out_refund').mapped('invoice_line_ids').filtered(
                lambda l: l.product_id.id == refund.product_id.id)
            if lines:
                refund.make_refund_invoice(lines)
                refund.refund_id.compute_taxes()
                refund.refund_id.action_invoice_open()

    def _get_refund_invoice_vals(self, invoice):
        return {
                'partner_id': invoice.partner_id.id,
                'fiscal_position_id':
                    invoice.fiscal_position_id.id,
                'date_invoice': datetime.now(),
                'journal_id': invoice.journal_id.id,
                'account_id':
                    invoice.partner_id.property_account_receivable_id.id,
                'currency_id':
                    invoice.currency_id.id,
                'company_id': invoice.company_id.id,
                'user_id': self.env.user.id,
                'type': 'out_refund',
                'payment_term_id': False,
                'payment_mode_id':
                    invoice.payment_mode_id.id,
                'name': invoice.name,
                'amazon_order': invoice.amazon_order.id,
            }

    @api.multi
    def make_refund_invoice(self, invoice_lines):
        refunds = self.env['account.invoice']
        for amazon_refund_obj in self:
            if not invoice_lines:
                return
            invoice = invoice_lines[0].invoice_id
            header_vals = self._get_refund_invoice_vals(invoice)
            refund_invoice = self.env['account.invoice'].create(header_vals)
            for invoice_line in invoice_lines:
                vals = {
                    'invoice_id': refund_invoice.id,
                    'name': invoice_line.name,
                    'product_id': invoice_line.product_id.id,
                    'account_id': invoice_line.account_id.id,
                    'quantity': amazon_refund_obj.product_qty or 1,
                    'price_unit': invoice_line.price_unit,
                    'cost_unit': invoice_line.cost_unit,
                    'discount': invoice_line.discount,
                    'account_analytic_id': False,
                    'invoice_line_tax_ids': [(6, 0, invoice_line.invoice_line_tax_ids.ids)]
                }
                amazon_refund_obj.price_unit = invoice_line.price_unit
                self.env['account.invoice.line'].create(vals)
            amazon_refund_obj.write({'state': 'refund_created', 'refund_id': refund_invoice.id})
            refunds += refund_invoice
        return refunds

    @api.multi
    def retry_refund(self):
        for refund in self:
            if not refund.product_id:
                refund.product_id = self.env['product.product'].search(
                    [('asin_code', '=', refund.asin_code)]).id or False
            if not refund.amazon_order_id:
                refund.amazon_order_id = self.env['amazon.sale.order'].search(
                    [('name', '=', refund.amazon_order_name)]).id or False
            error_message = refund.check_errors()
            if error_message:
                refund.error_message = error_message
                continue
            refund.process_refund()
