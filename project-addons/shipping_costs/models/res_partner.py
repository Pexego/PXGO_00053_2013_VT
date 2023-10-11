from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    shipping_cost_id = fields.One2many("shipping.cost", "transporter_id")
    zone_id = fields.One2many("shipping.zone", "transporter_id")
