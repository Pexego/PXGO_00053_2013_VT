from odoo import models, fields, api, exceptions, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amazon_order = fields.Many2one(comodel_name='amazon.sale.order')
    amazon_invoice = fields.Char()
    tax_in_price_unit = fields.Boolean()

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
    def _is_sii_simplified_invoice(self):
        res = super(AccountInvoice, self)._is_sii_simplified_invoice()
        return res and not self.partner_id.amazon_parent_id


class AccountMove(models.Model):
    _inherit = 'account.move'

    amazon_settlement_id = fields.Many2one("amazon.settlement")
    amazon_refund_settlement_id = fields.Many2one("amazon.settlement")


