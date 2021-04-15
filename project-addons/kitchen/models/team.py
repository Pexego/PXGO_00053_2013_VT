from odoo import models, _, api, fields, exceptions


class CRMTeam(models.Model):
    _inherit = 'crm.team'

    email = fields.Char()

