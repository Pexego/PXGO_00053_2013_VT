from odoo import models, fields


class Transporter(models.Model):
    _inherit = "transportation.transporter"

    weight_volume_translation = fields.Float(string="Translation (kg/cbm)")
