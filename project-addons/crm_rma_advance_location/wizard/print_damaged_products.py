from odoo import fields, models, api, exceptions, _


class PrintClaimLineWizard(models.TransientModel):
    _name = "print.claim.line.wizard"

    @api.model
    def _get_lines(self):
        return self.env['claim.line'].browse(self.env.context['active_ids'])

    claim_line_ids = fields.Many2many('claim.line',
                                        'print_claim_line_id',
                                        'claim_line', default=_get_lines)

    def print(self):
        self.claim_line_ids.write({"printed": True})
        return self.env.ref('crm_rma_advance_location.report_print_claim_line').report_action(self.claim_line_ids.ids,
                                                                                              config=False)