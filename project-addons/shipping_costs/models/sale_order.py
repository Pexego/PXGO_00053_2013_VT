from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    shipping_cost_id = fields.One2many("shipping.cost", "sale_order_id", string="Fee")
