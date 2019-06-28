# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class AccountAccount(models.Model):

    _inherit = 'account.account'

    circulating = fields.Boolean()
