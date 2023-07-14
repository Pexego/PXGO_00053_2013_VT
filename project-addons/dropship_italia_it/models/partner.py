from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    dropship = fields.Boolean('Dropship')
