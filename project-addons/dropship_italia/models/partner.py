from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    transporter_dropship = fields.Boolean('Dropship')
