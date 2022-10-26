from odoo import models, fields


class ClaimLine(models.Model):

    _inherit = 'claim.line'

    printable_test = fields.Boolean("Printable", default=True)
