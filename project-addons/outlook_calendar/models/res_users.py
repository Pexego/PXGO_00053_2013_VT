
from odoo import models, api, fields
from requests_oauthlib import OAuth2Session


class ResUsers(models.Model):
    _inherit = 'res.users'

    outlook_auth_token = fields.Char('Outlook token')
    outlook_auth_state = fields.Char()

    @api.multi
    def get_outlook_auth(self):
        client_id = self.env['ir.config_parameter'].sudo().get_param('outlook.client.id')
        scope = ['Calendars.ReadWrite']

        oauth = OAuth2Session(client_id, scope=scope)
        authorization_url, state = oauth.authorization_url(
            'https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize')
        self.env.user.outlook_auth_state = state

        return {
            'type': 'ir.actions.act_url',
            'view_type': 'form',
            'url': authorization_url,
            'target': 'new'
        }



