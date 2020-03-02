from odoo import api, exceptions, fields, models, _
import re


class MailActivity(models.Model):
    _inherit = 'mail.activity'
    sync_with_calendar = fields.Boolean('Create calendar event')
    calendar_start = fields.Datetime('Start')
    calendar_stop = fields.Datetime('End')

    @api.multi
    def action_close_dialog(self):
        if self.sync_with_calendar and self.env.context.get('default_res_model') == 'crm.lead':
            lead = self.env['crm.lead'].browse(self.env.context.get('default_res_id'))
            partners = [[6, False, []]]
            if self.user_id.id != self.env.user.id:
                partners[0][2].append(self.user_id.partner_id.id)
            partners[0][2].append(self.env.user.partner_id.id)
            vals = {
                "name": self.activity_type_id.name + " - " + (self.summary or ''),
                "description": lead.name + " - " + lead.partner_id.name + " - " + re.sub(r'<[^>]*?>', '', self.note),
                "start": self.calendar_start,
                "stop": self.calendar_stop,
                "user_id": self.env.user.id,
                "partner_ids": partners
            }
            self.env['calendar.event'].create(vals)

        return super().action_close_dialog()
