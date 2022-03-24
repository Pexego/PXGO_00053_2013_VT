from odoo import models, fields, api, _, exceptions
from datetime import datetime


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

    @api.multi
    def _check_duplicate_supplier_reference(self):
        for invoice in self:
            # refuse to validate a vendor bill/credit note if there already exists one with the same reference for the same partner,
            # because it's probably a double encoding of the same bill/credit note
            # NEW: In italy, it is allowed if the invoices are from different years
            if invoice.type in ('in_invoice', 'in_refund') and invoice.reference:
                invs = self.search([('type', '=', invoice.type),
                                ('reference', '=', invoice.reference),
                                ('company_id', '=', invoice.company_id.id),
                                ('commercial_partner_id', '=', invoice.commercial_partner_id.id),
                                ('id', '!=', invoice.id)])
                for inv in invs:
                    if datetime.strptime(inv.date,"%Y-%m-%d").year == datetime.today().year:
                        raise exceptions.UserError(_("Duplicated vendor reference detected. You probably encoded twice the same vendor bill/credit note."))


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


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    @api.multi
    @api.depends("mandate_id")
    def _get_partner_bank(self):
        for line in self:
            line.bank_id = line.mandate_id.partner_bank_id.bank_id

    bank_id = fields.Many2one("res.bank", "Bank", compute="_get_partner_bank", store=True)

