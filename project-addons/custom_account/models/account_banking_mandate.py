from odoo import models, fields, api


class AccountBankingMandate(models.Model):

    _inherit = 'account.banking.mandate'

    @api.multi
    @api.depends('unique_mandate_reference', 'recurrent_sequence_type')
    def compute_display_name(self):
        super(AccountBankingMandate, self).compute_display_name()
        for mandate in self:
            if mandate.format == 'sepa':
                name = '%s (%s) [%s]' % (
                    mandate.unique_mandate_reference,
                    mandate.recurrent_sequence_type,
                    mandate.partner_bank_id.acc_number)
            else:
                name = mandate.unique_mandate_reference
            mandate.display_name = name

    @api.multi
    def cancel(self):
        res = super().cancel()
        for mandate in self:
            if all(mandate.state == 'cancel' for mandate in mandate.partner_bank_id.mapped('mandate_ids')):
                mandate.partner_bank_id.active = False
        return res

