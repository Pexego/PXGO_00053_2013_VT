from odoo import http
from odoo.http import request
from requests_oauthlib import OAuth2Session


class OutlookCalendarController(http.Controller):

    @http.route('/outlook_calendar/get_token', type='http', auth='user')
    def return_url_outlook(self, **kw):
        client_id = request.env['ir.config_parameter'].sudo().get_param('outlook.client.id')
        client_secret = request.env['ir.config_parameter'].sudo().get_param('outlook.client.secret')
        authorization_response = 'http://localhost:9169/outlook_calendar/get_token?code='+kw['code']+'&state='+kw['state']+'&session_state='+kw['session_state']

        outlook = OAuth2Session(client_id, state=request.env.user.outlook_auth_state)
        token = outlook.fetch_token(
            'https://login.microsoftonline.com/organizations/oauth2/v2.0/token',
            authorization_response=authorization_response,
            client_secret=client_secret)
        request.env.user.outlook_auth_token = token['access_token']
        return ''
