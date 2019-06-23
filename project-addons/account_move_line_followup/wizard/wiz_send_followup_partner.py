# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from datetime import datetime


class WizSendFollowupPartner(models.TransientModel):
    _name = 'wiz.send.followup.partner'
    _description = 'Send followup communication'

    level_id = fields.Many2one('credit.control.policy.level', 'Followup Level', required=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)

    @api.multi
    def preview_partner_followup_email(self):
        partner_id = self.env['res.partner'].browse(self._context.get('active_ids', []))
        communication_obj = self.env['credit.control.communication']
        composer_form_view_id = self.env.ref('mail.email_compose_message_wizard_form').id

        # Search all manual communications for this partner
        comm_manual = communication_obj.search(
            [('partner_id', '=', partner_id.id),
             ('email_type', '=', 'manual')])
        # Search manual communications with email sent
        comm_with_email = communication_obj.search(
            [('partner_id', '=', partner_id.id),
             ('email_type', '=', 'manual'),
             ('message_ids.message_type', 'in', ['comment'])])
        # The difference: manual communications without email sent
        comm_without_email = set(tuple(comm_manual)) - set(tuple(comm_with_email))

        if comm_without_email:
            # Use that draft communication to generate a email preview
            communication_id = tuple(comm_without_email)[0]
            communication_id.write({
                'report_date': datetime.now().strftime('%Y-%m-%d'),
                'current_policy_level': self.level_id.id
            })
        else:
            communication_id = communication_obj.create({
                'partner_id': partner_id.id,
                'current_policy_level': self.level_id.id,
                'currency_id': self.env.user.company_id.currency_id.id,
                'email_type': 'manual'
            })

        move_lines = communication_id._get_unreconciled_move_lines()
        communication_id.write({'move_line_ids': [(6, 0, move_lines.ids)]})

        template_id = self.level_id.email_template_id
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'view_id': composer_form_view_id,
            'target': 'new',
            'context': {
                'default_composition_mode': 'comment',
                'default_res_id': communication_id.id,
                'default_model': 'credit.control.communication',
                'default_use_template': bool(template_id.id),
                'default_template_id': template_id.id,
                'website_sale_send_recovery_email': True,
                'active_ids': communication_id.id,
            },
        }

