from odoo import models, api, fields


class OutlookCalendar(models.Model):

    _name = 'outlook.calendar'

    name = fields.Char('Name', readonly=True)
    outlook_id = fields.Char(readonly=True)
    sync = fields.Boolean('Sync')
    can_edit = fields.Boolean(readonly=True)
    user_id = fields.Many2one('res.user', readonly=True)
