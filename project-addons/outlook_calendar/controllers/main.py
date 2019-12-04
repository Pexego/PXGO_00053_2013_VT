from odoo import http
from odoo.http import request
from requests_oauthlib import OAuth2Session
from datetime import datetime
from dateutil.relativedelta import relativedelta
import werkzeug


class OutlookCalendarController(http.Controller):

    @http.route('/outlook_calendar/get_token', type='http', auth='user')
    def return_url_outlook(self, **kw):
        client_id = request.env['ir.config_parameter'].sudo().get_param('outlook.client.id')
        client_secret = request.env['ir.config_parameter'].sudo().get_param('outlook.client.secret')
        authorization_response = 'http://localhost:9169/outlook_calendar/get_token?code=' \
                                 + kw['code'] + '&state=' + kw['state'] + '&session_state=' + kw['session_state']

        outlook = OAuth2Session(client_id, state=request.env.user.outlook_auth_state)

        token = outlook.fetch_token(
            'https://login.microsoftonline.com/organizations/oauth2/v2.0/token',
            authorization_response=authorization_response,
            client_secret=client_secret,
            response_type='id_token')

        request.env.user.outlook_auth_token = token['access_token']
        request.env.user.outlook_auth_refresh_token = token['refresh_token']
        request.env.user.outlook_auth_token_exp = datetime.now() + relativedelta(seconds=token['expires_in'])
        request.env.user.get_outlook_calendars()

        request.env.user.with_delay(priority=20, eta=token['expires_in']-120).refresh_outlook_token()

        return werkzeug.utils.redirect("/web")
