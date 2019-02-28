# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class IrAttachment(models.Model):

    _inherit = "ir.attachment"

    to_print = fields.Boolean()
