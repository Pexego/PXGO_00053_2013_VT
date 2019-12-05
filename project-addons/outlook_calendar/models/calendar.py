from odoo import api, fields, models, _
import requests
import json


class CalendarEvent(models.Model):

    _inherit = "calendar.event"

    outlook_id = fields.Char()
    outlook_calendar_id = fields.Many2one('outlook.calendar', domain=[('can_edit', '=', True)], auto_join=True)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if self.env.user.outlook_sync and 'outlook_id' not in vals:
            auth = self.env.user.outlook_auth_token
            if self.env.user.partner_id.id in vals['partner_ids'][0][2]:
                partner_ids = vals['partner_ids'][0][2].remove(self.env.user.partner_id.id)
            else:
                partner_ids = vals['partner_ids'][0][2]
            partners = self.env['res.partner'].browse(partner_ids)
            attendees = []
            for partner in partners:
                if partner.email.endswith("@visiotechsecurity.com"):
                    attendees.append({
                                        "emailAddress": {
                                            "address": partner.email,
                                            "name": partner.name
                                        },
                                        "type": "required"
                                    })

            event_data = {
                            "subject": vals['name'],
                            "body": {
                                        "contentType": "HTML",
                                        "content": vals['description'] or ""
                                    },
                            "start": {
                                "dateTime": vals['start_datetime'][:10] + 'T' + vals['start_datetime'][11:],
                                "timeZone": "Romance Standard Time"
                            },
                            "end": {
                                "dateTime": vals['stop_datetime'][:10] + 'T' + vals['stop_datetime'][11:],
                                "timeZone": "Romance Standard Time"
                            },
                            "attendees": attendees
                        }
            response = requests.post('https://graph.microsoft.com/v1.0/me/events',
                                     headers={'Authorization': 'Bearer ' + auth}, json=event_data)
            if response.status_code == 201:
                o_event = json.loads(response.text)
                res.outlook_id = o_event['id']
            elif response.status_code == 401:
                message = _("The event hasn't been created in Outlook. \nPlease log in in your profile")
                self.env.user.notify_warning(message=message)
        return res

    @api.multi
    def unlink(self):
        if self.env.user.outlook_sync:
            auth = self.env.user.outlook_auth_token
            response = requests.delete('https://graph.microsoft.com/v1.0/me/events/%s' % self.outlook_id,
                                       headers={'Authorization': 'Bearer ' + auth})
            if response.status_code == 401:
                message = _("The event hasn't been deleted in Outlook. Please log in in your profile")
                self.env.user.notify_warning(message=message)
        return super().unlink()

    @api.model
    def write(self, vals):
        print(vals)
        res = super().write(vals)
        return res
