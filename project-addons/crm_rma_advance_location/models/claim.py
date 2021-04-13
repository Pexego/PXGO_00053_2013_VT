from odoo import fields, models


class CrmClaimRma(models.Model):

    _inherit = 'claim.line'

    printed = fields.Boolean()

