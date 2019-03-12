# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class MinimumDay(models.Model):
    _name = 'minimum.day'
    _description = 'Setting minimum stock days'

    name = fields.Char(size=255, required=True)
    days_sale = fields.Float('Security Days', required=True)
    default = fields.Boolean(default=True)
