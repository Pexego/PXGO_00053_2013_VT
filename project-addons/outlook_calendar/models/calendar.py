from odoo import api, fields, models, _
import requests
import json


class CalendarEvent(models.Model):

    _inherit = "calendar.event"

    outlook_id = fields.Char()
    outlook_calendar_id = fields.Many2one('outlook.calendar', 'Outlook calendar',
                                          domain=[('can_edit', '=', True)], auto_join=True)
    outlook_last_modified_datetime = fields.Datetime()

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if self.env.user.outlook_sync and 'outlook_id' not in vals:
            auth = self.env.user.outlook_auth_token
            attendees = []
            if 'partner_ids' in vals:
                if self.env.user.partner_id.id in vals['partner_ids'][0][2]:
                    partner_ids = vals['partner_ids'][0][2].remove(self.env.user.partner_id.id)
                else:
                    partner_ids = vals['partner_ids'][0][2]
                partners = self.env['res.partner'].browse(partner_ids)
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
                            "subject": vals.get('name', ''),
                            "body": {
                                        "contentType": "HTML",
                                        "content": vals.get('description', '') and vals.get('description') or ''
                                    },
                            "start": {
                                "dateTime": vals['start'][:10] + 'T' + vals['start'][11:],
                                "timeZone": "GMT Standard Time"
                            },
                            "end": {
                                "dateTime": vals['stop'][:10] + 'T' + vals['stop'][11:],
                                "timeZone": "GMT Standard Time"
                            },
                            "attendees": attendees
                        }
            response = requests.post('https://graph.microsoft.com/v1.0/me/events',
                                     headers={'Authorization': 'Bearer ' + auth}, json=event_data)
            if response.status_code == 201:
                o_event = json.loads(response.text)
                res.outlook_id = o_event['id']
                res.outlook_last_modified_datetime = o_event['lastModifiedDateTime'][:-9].replace('T', ' ')
            elif response.status_code == 401:
                message = _("The event hasn't been created in Outlook. Please log in in your profile")
                self.env.user.notify_warning(message=message)
        return res

    @api.multi
    def unlink(self):
        if self.env.user.outlook_sync and self.outlook_id and not self.env.context.get('outlook_to_delete', False):
            # if the outlook_to_delete in the context is true, there's no need of delete the event again in outlook
            auth = self.env.user.outlook_auth_token
            response = requests.delete('https://graph.microsoft.com/v1.0/me/events/%s' % self.outlook_id,
                                       headers={'Authorization': 'Bearer ' + auth})
            if response.status_code == 401:
                message = _("The event hasn't been deleted in Outlook. Please log in in your profile")
                self.env.user.notify_warning(message=message)
        return super().unlink()

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if self.env.user.outlook_sync and 'outlook_id' not in vals and self.outlook_id:
            auth = self.env.user.outlook_auth_token
            up_fields = ['location', 'name', 'start', 'stop', 'partner_ids']
            event_data = {}

            for field in up_fields:
                if field in vals:
                    if field == 'location':
                        event_data['location'] = {
                            "displayName": vals['location']
                        }
                    elif field == 'name':
                        event_data['subject'] = vals['name']
                    elif field == 'start':
                        event_data['start'] = {
                            "dateTime": vals['start'].replace(' ', 'T'),
                            "timeZone": "GMT Standard Time"
                        }
                    elif field == 'stop':
                        event_data['end'] = {
                            "dateTime": vals['stop'].replace(' ', 'T'),
                            "timeZone": "GMT Standard Time"
                        }
                    elif field == 'partner_ids':
                        partners_vals = vals['partner_ids'][0][2]
                        if self.env.user.partner_id.id in vals['partner_ids'][0][2]:
                            partners_vals.remove(self.env.user.partner_id.id)
                        attendees = []
                        partners = self.env['res.partner'].browse(partners_vals)
                        for partner in partners:
                            if partner.email.endswith("@visiotechsecurity.com"):
                                attendees.append({
                                    "emailAddress": {
                                        "address": partner.email,
                                        "name": partner.name
                                    },
                                    "type": "required"
                                })
                        event_data['attendees'] = attendees

            response = requests.patch('https://graph.microsoft.com/v1.0/me/events/%s' % self.outlook_id,
                                      headers={'Authorization': 'Bearer ' + auth}, json=event_data)

            if response.status_code == 401:
                message = _("The event hasn't been updated in Outlook. Please log in in your profile")
                self.env.user.notify_warning(message=message)

        return res
