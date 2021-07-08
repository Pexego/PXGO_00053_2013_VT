from odoo import models, fields, api, exceptions, _


class CrmClaimInvoiceDiscount(models.TransientModel):
    _name = 'invoice.discount.wiz'

    # crm_claim_line_ids = fields.One2many('invoice.discount.wiz.line', 'wizard_id',
    #                             string="CRM Claim Line")
    
    origin_reference = fields.Reference(
        lambda self: [
            (m.model, m.name) for m in self.env['ir.model'].search([])],
        string='Object')
    continue_method = fields.Char()
    message = fields.Char(string='Message', readonly=True)


    @api.multi
    def action_show(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Crm Claim Invoice Discount'),
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.multi
    def button_continue(self):
        self.ensure_one()
        return getattr(self.origin_reference.with_context(), self.continue_method)()

# class CrmClaimInvoiceDiscount(models.TransientModel):
#     _name = 'invoice.discount.wiz.line'

#     wizard_id = fields.Many2one('invoice.discount.wiz')
#     invoice_id = fields.Many2one('account.invoice', "Invoice", readonly=True)
#     product_id = fields.Many2one('product.product', "Product", readonly=True)
#     product_description = fields.Char(string="Description")
#     qty = fields.Float()
#     price_unit = fields.Float("Price per Unit",default=0,required=True)
#     discount = fields.Float("Discount",default=0.0,required=True)
#     tax_ids = fields.Many2one('account.tax', "Product", readonly=True)
#     price_subtotal = fields.Float("Price Subtotal", readonly=True)
#     invoiced = fields.Boolean(string="Invoiced")