from odoo import models, api, fields, _
from requests_oauthlib import OAuth2Session
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.addons.queue_job.job import job
import requests
import json


class ResUsers(models.Model):
    _inherit = 'res.users'

    outlook_auth_token = fields.Char('Outlook token')
    outlook_auth_token_exp = fields.Datetime('Expiration date')
    outlook_auth_refresh_token = fields.Char('Outlook refresh token')
    outlook_auth_state = fields.Char()
    outlook_is_logged = fields.Boolean('Logged in Outlook', compute='_get_is_outlook_logged')
    outlook_calendar_ids = fields.One2many('outlook.calendar', 'user_id')
    outlook_sync = fields.Boolean('Activate Outlook Sync')

    def _get_is_outlook_logged(self):
        if self.outlook_auth_token and self.outlook_auth_refresh_token and \
                datetime.strptime(self.outlook_auth_token_exp, '%Y-%m-%d %H:%M:%S') > datetime.now():

            self.outlook_is_logged = True
        else:
            self.outlook_is_logged = False

    @api.multi
    def get_outlook_auth(self):
        client_id = self.env['ir.config_parameter'].sudo().get_param('outlook.client.id')
        scope = ['offline_access', 'Calendars.ReadWrite']

        oauth = OAuth2Session(client_id, scope=scope)
        authorization_url, state = oauth.authorization_url(
            'https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize')
        self.env.user.outlook_auth_state = state
        self.outlook_sync = True

        return {
            'type': 'ir.actions.act_url',
            'view_type': 'form',
            'url': authorization_url,
            'target': 'new'
        }

    @job()
    @api.multi
    def refresh_outlook_token(self):
        client_id = self.env['ir.config_parameter'].sudo().get_param('outlook.client.id')
        client_secret = self.env['ir.config_parameter'].sudo().get_param('outlook.client.secret')

        outlook = OAuth2Session(client_id, state=self.env.user.outlook_auth_state)

        token = outlook.refresh_token(
            'https://login.microsoftonline.com/organizations/oauth2/v2.0/token',
            refresh_token=self.env.user.outlook_auth_refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            response_type='id_token')

        self.env.user.outlook_auth_token = token['access_token']
        self.env.user.outlook_auth_refresh_token = token['refresh_token']
        self.env.user.outlook_auth_token_exp = datetime.now() + relativedelta(seconds=token['expires_in'])
        self.env.user.with_delay(priority=20, eta=token['expires_in'] - 120).refresh_outlook_token()

    @api.multi
    def get_outlook_calendars(self):
        auth = self.env.user.outlook_auth_token

        response = requests.get('https://graph.microsoft.com/v1.0/me/calendars',
                                headers={'Authorization': 'Bearer ' + auth})

        if response.status_code == 200:
            calendars = json.loads(response.text)
            for calendar in calendars['value']:
                new_calendars = []
                if calendar['id'] not in self.outlook_calendar_ids.mapped('outlook_id'):
                    new_calendars.append((0, 0, {'name': calendar['name'],
                                                 'outlook_id': calendar['id'],
                                                 'can_edit': calendar['canEdit'],
                                                 'sync': False,
                                                 'user_id': self.id}))
                    self.write({'outlook_calendar_ids': new_calendars})
        elif response.status_code == 401:
            message = _("Imposible to sync your calendars from Outlook. Please log in in your profile")
            self.env.user.notify_warning(message=message)

    @api.multi
    def sync_outlook_calendar(self):
        # Get all events from now to 30 days ahead. TODO: maybe change 30 days to the whole future?
        if self.outlook_sync:
            auth = self.env.user.outlook_auth_token
            startdatetime = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            enddatetime = (datetime.now() + relativedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S')

            response = requests.get('https://graph.microsoft.com/v1.0/me/calendarview?startdatetime=%s&enddatetime=%s'
                                    % (startdatetime, enddatetime),
                                    headers={'Authorization': 'Bearer ' + auth,
                                             'Prefer': 'outlook.timezone="Romance Standard Time"'})

            if response.status_code == 200:
                events = json.loads(response.text)
                for event in events['value']:
                    if event['id'] not in self.env['calendar.event'].search([('user_id', '=', self.id)]).mapped('outlook_id'):
                        stop = event['end']['dateTime'][:-1].replace('T', ' ')
                        start = event['start']['dateTime'][:-1].replace('T', ' ')
                        new_event_vals = {
                            'name': event['subject'] or "",
                            'outlook_id': event['id'],
                            'location': event['location']['displayName'] or "",
                            'start': start,
                            'stop': stop
                        }
                        self.env['calendar.event'].create(new_event_vals)
            elif response.status_code == 401:
                message = _("Imposible to sync your events from Outlook. Please log in in your profile")
                self.env.user.notify_warning(message=message)

        action = self.env.ref('calendar.action_calendar_event').read()[0]
        return action
