from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    no_promos = fields.Boolean(string="Not apply promotions")
