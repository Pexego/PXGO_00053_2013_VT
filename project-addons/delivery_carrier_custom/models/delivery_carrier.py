from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    by_air = fields.Boolean()
    partner_id = fields.Many2one(domain=[('is_transporter', '=', True)])
