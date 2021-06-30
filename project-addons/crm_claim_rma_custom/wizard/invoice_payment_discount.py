from odoo import models, fields, api, exceptions, _


class CrmClaimInvoiceDiscount(models.TransientModel):
    _name = 'crm.claim.invoice.discount'

    def _get_discount_line(self):
        wiz_lines = []
        crm_obj = self.env['crm.claim']
        crm_ids = self.env.context.get('active_ids', [])
        crms = crm_obj.search([('id', 'in', crm_ids)])
        for crm in crms:
            for crm_inv_line_id in crm.claim_inv_line_ids:
                wiz_lines.append({'invoice_id': crm_inv_line_id.invoice_id,
                                    'product_id': crm_inv_line_id.product_id,
                                    'product_description': crm_inv_line_id.product_description,
                                    'qty': crm_inv_line_id.qty,
                                    'price_unit': crm_inv_line_id.price_unit,
                                    'discount': crm_inv_line_id.discount,
                                    'tax_ids': crm_inv_line_id.tax_ids,
                                    'price_subtotal': crm_inv_line_id.price_subtotal,
                                    'invoiced': crm_inv_line_id.invoiced})
        return wiz_lines

    crm_claim_line_ids = fields.One2many('crm.claim.invoice.discount.line', 'wizard_id',
                                 string="CRM Claim Line", default=_get_discount_line)

class CrmClaimInvoiceDiscount(models.TransientModel):
    _name = 'crm.claim.invoice.discount.line'

    wizard_id = fields.Many2one('crm.claim.invoice.discount')
    invoice_id = fields.Many2one('account.invoice', "Product", readonly=True)
    product_id = fields.Many2one('product.product', "Product", readonly=True)
    product_description = fields.Char(string="Description")
    qty = fields.Float()
    price_unit = fields.Float("Price per Unit",default=0,required=True)
    discount = fields.Float("Discount",default=0.0,required=True)
    tax_ids = fields.Many2one('account.tax', "Product", readonly=True)
    price_subtotal = fields.Float("Price Subtotal", readonly=True)
    invoiced = fields.Boolean(string="Invoiced")