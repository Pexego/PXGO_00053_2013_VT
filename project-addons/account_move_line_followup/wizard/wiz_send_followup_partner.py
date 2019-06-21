# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class WizSendFollowupPartner(models.TransientModel):
    _name = 'wiz.send.followup.partner'
    _description = 'Send followup communication'

    level_id = fields.Many2one('credit.control.policy.level', 'Level', required=True)
    communication_id = fields.Many2one('credit.control.communication')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)

    @api.multi
    def preview_partner_followup_email(self):
        partner_id = self.env['res.partner'].browse(self._context.get('active_ids', []))
        composer_form_view_id = self.env.ref('mail.email_compose_message_wizard_form').id
        if not self.level_id:
            # Return warning required level policy
            pass
        self.communication_id = self.env['credit.control.communication']. create({
            'partner_id': partner_id.id,
            'current_policy_level': self.level_id.id,
            'currency_id': self.env.user.company_id.currency_id.id
        })
        move_lines = self.communication_id._get_unreconciled_move_lines()
        self.communication_id.write({'move_line_ids': [(6, 0, move_lines.ids)]})

        template_id = self.level_id.email_template_id
        """email_values = template.generate_email(self.communication_id.id)
        self.email_body = email_values['body_html']

        return {"type": "ir.actions.do_nothing"}"""
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'view_id': composer_form_view_id,
            'target': 'new',
            'context': {
                'default_composition_mode': 'comment',
                'default_res_id': self.communication_id.id,
                'default_model': 'credit.control.communication',
                'default_use_template': bool(template_id.id),
                'default_template_id': template_id.id,
                'website_sale_send_recovery_email': True,
                'active_ids': self.communication_id.id,
            },
        }



