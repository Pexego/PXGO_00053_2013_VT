from odoo import models, fields


class Transporter(models.Model):

    _inherit = 'transportation.transporter'

    dropship = fields.Boolean('Dropship')


class TransportService(models.Model):

    _inherit = 'transportation.service'

    dropship = fields.Boolean('Dropship')
