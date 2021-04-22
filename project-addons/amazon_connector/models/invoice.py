from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amazon_order = fields.Many2one(comodel_name='amazon.sale.order')

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        for invoice in self:
            if invoice.amazon_order:
                invoice.amazon_order.state= "invoice_open"
        return res


