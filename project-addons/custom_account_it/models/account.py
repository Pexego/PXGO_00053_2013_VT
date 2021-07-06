from odoo import models, fields, api, _, exceptions


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def _get_document_fiscal_type(self, type=None, partner=None,
                                  fiscal_position=None, journal=None):
        dt = super()._get_document_fiscal_type(type=type, partner=partner,
                                               fiscal_position=fiscal_position, journal=journal)
        doc_id = False
        if type == 'out_refund':
            doc_id = self.env['fiscal.document.type'].search(
                    [('id', '=', self.env.ref('l10n_it_fiscal_document_type.2').id)], limit=1).id
        if doc_id and doc_id not in dt:
            dt.insert(0, doc_id)
        return dt


class AccountBankingMandate(models.Model):

    _inherit = 'account.banking.mandate'

    format = fields.Selection(
        selection_add=[('riba', 'RiBa Mandate')])


class GroupRiba(models.Model):

    _inherit = "res.partner"

    @api.onchange("customer_payment_mode_id")
    def on_change_customer_payment_mode_id(self):
        if self.customer_payment_mode_id.name == "Ricevuta bancaria":
            self.group_riba = True