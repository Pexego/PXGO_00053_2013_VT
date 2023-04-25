from odoo import models, api, fields, exceptions, _

class CrmClaimPendingWizardLine(models.TransientModel):
    _name = 'crm.claim.pending.wizard.line'

    choose = fields.Boolean('Add')
    claim_id = fields.Many2one('crm.claim', 'Claim')
    claim_id_ro = fields.Many2one('crm.claim', 'Claim', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    partner_shipping_id = fields.Many2one('res.partner', 'Shipping', readonly=True)
    wizard_id = fields.Many2one('crm.claim.pending.wizard')


class CrmClaimPendingWizard(models.TransientModel):
    _name = 'crm.claim.pending.wizard'

    @api.model
    def _get_pending_claims(self):
        wiz_lines = []
        claim = self.env['crm.claim'].browse(self.env.context.get('active_ids'))
        stage_sale_attach_id = self.env['crm.claim.stage'].search([('name', '=', 'Adjuntar con pedido')]).id
        pending_rmas = self.env['crm.claim'].search(
            [('partner_id', '=', claim.partner_id.id), ('stage_id', '=', stage_sale_attach_id),
             ('delivery_address_id', '=', claim.delivery_address_id.id)])

        for rma in pending_rmas:
            new_line = {'choose': False,
                        'claim_id': rma.id,
                        'claim_id_ro': rma.id,
                        'partner_id': rma.partner_id,
                        'partner_shipping_id': rma.delivery_address_id}
            wiz_lines.append(new_line)
        return wiz_lines

    line_ids = fields.One2many('crm.claim.pending.wizard.line', 'wizard_id', default=_get_pending_claims)

    def add_to_claim(self):
        claim = self.env['crm.claim'].browse(self.env.context.get('active_ids'))
        state = self.env.ref('crm_claim_rma_custom.stage_claim_pending_rev')
        notes = claim.internal_notes or ''
        for rma in self.line_ids.filtered(lambda l: l.choose):
            notes += _('\n Add %s  Ub.: %s') % (rma.claim_id.number, rma.claim_id.location)
            rma.claim_id.stage_id = state.id
            rma.claim_id.att_claim_id = claim.id
        if notes:
            claim.internal_notes = notes
