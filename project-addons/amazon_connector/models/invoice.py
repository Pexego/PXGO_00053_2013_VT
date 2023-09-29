from odoo import models, fields, api, exceptions, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amazon_order = fields.Many2one(comodel_name='amazon.sale.order')
    marketplace_id = fields.Many2one(related="amazon_order.sales_channel")
    amazon_invoice = fields.Char()
    tax_in_price_unit = fields.Boolean()
    amazon_sale_refund_ids = fields.One2many("amazon.sale.refund", "refund_id")
    date_amazon_first_refund = fields.Date(compute="_get_date_amazon_first_refund")

    @api.multi
    def _get_date_amazon_first_refund(self):
        for invoice in self:
            invoice.date_amazon_first_refund = invoice.amazon_sale_refund_ids[0].refund_date\
                if invoice.amazon_sale_refund_ids else False

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        for invoice in self:
            if invoice.amazon_order:
                amazon_order = invoice.amazon_order
                amazon_order.state = "invoice_open"
        return res

    @api.multi
    def do_merge(self, keep_references=True, date_invoice=False,
                 remove_empty_invoice_lines=True):
        res = super(AccountInvoice, self).do_merge(keep_references,date_invoice,remove_empty_invoice_lines)
        amazon_order = self.mapped('amazon_order')
        if res and amazon_order:
            if len(amazon_order)>1:
                raise exceptions.Warning(_('You cannot merge invoices with differents amazon orders: %s') %amazon_order.mapped('name'))
            invoice = self.env['account.invoice'].browse(list(res))
            invoice.write({'name':amazon_order.name,'amazon_order':amazon_order.id,'amazon_invoice':amazon_order.amazon_invoice_name})
        return res

    @api.multi
    @api.depends('amazon_order', 'amazon_order.amazon_company_id','amazon_order.amazon_company_id.sii_enabled')
    def _compute_sii_enabled(self):
        """Inherit original function to disable sending to the sii depending on the amazon company"""
        super()._compute_sii_enabled()
        for invoice in self:
            amazon_order = invoice.amazon_order
            if amazon_order:
                invoice.sii_enabled = not amazon_order.amazon_company_id or amazon_order.amazon_company_id.sii_enabled



class AccountMove(models.Model):
    _inherit = 'account.move'

    amazon_settlement_id = fields.Many2one("amazon.settlement")
    amazon_refund_settlement_id = fields.Many2one("amazon.settlement")


