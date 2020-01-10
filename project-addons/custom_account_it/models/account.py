from odoo import models, fields, api, _, exceptions

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        if vals.get('type', False) == "out_refund":
            vals["fiscal_document_type_id"] = self.env['fiscal.document.type'].search(
                    [('name', 'like', 'nota di credito')], limit=1).id
        return super().create(vals)

    @api.onchange('partner_id', 'journal_id', 'type', 'fiscal_position_id')
    def _set_document_fiscal_type_out_refund(self):
        if self.type == 'out_refund':
            self.fiscal_document_type_id = self.env['fiscal.document.type'].search(
                [('name', 'like', 'nota di credito')], limit=1).id