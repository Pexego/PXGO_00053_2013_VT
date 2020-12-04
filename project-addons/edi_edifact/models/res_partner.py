from odoo import models, fields


class ResPartner(models.Model):

    _inherit = "res.partner"

    ean = fields.Char('EDI EAN')
