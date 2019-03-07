# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    cyc_notify_date = fields.Date("C&C notify date")
    cyc_limit_date_insolvency = fields.Date("C&C limit date insolvency")
