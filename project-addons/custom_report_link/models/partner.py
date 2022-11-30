from odoo import models, fields


class Partner(models.Model):

    _inherit = "res.partner"

    explode_kits_in_pdf = fields.Boolean()
