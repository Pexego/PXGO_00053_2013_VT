from odoo import models, fields, _


class UpdatePartnerRisk(models.TransientModel):
    _inherit = 'update.partner.risk'

    def action_update_risk(self):
        super(UpdatePartnerRisk, self.with_context({'update_payment_mode': False})).action_update_risk()
        if self.new_risk == 0:
            for partner in self.partner_ids:
                partner.property_payment_term_id = self.env.ref('account.account_payment_term_immediate').id
                payment_mode = self.env['account.payment.mode'].search([('name', '=', 'Transferencia')])
                partner.customer_payment_mode_id = payment_mode.id

