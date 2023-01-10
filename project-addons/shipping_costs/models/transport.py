from odoo import models, fields


class Transporter(models.Model):
    _inherit = "transportation.transporter"

    shipping_cost_id = fields.One2many("shipping.cost", "transporter_id")
