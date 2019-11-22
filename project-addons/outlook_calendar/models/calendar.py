from odoo import api, fields, models
import requests


class CalendarEvent(models.Model):

    _inherit = "calendar.event"

    @api.model
    def create(self, vals):
        import ipdb
        ipdb.set_trace()
        res = super().create(vals)
        auth = self.env.user.outlook_auth_token
        graph_data = requests.get('https://graph.microsoft.com/v1.0/me/calendarview?startdatetime=2019-11-20T15:10:17.045Z&enddatetime=2019-11-27T15:10:17.045Z',
                                  headers={'Authorization': 'Bearer ' + auth}).json()
        print(graph_data)
        return res
