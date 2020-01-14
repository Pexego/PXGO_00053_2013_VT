from odoo import models, fields, api, _, exceptions

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        if vals.get('type', False) == "out_refund":
            vals["fiscal_document_type_id"] = self.env['fiscal.document.type'].search(
                    [('id', '=', self.env.ref('l10n_it_fiscal_document_type.2').id)], limit=1).id
        return super().create(vals)
