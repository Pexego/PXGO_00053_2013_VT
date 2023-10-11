from odoo import models, fields

class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    shipping_cost_supplement_id = fields.One2many("shipping.cost.supplement", "carrier_id")
