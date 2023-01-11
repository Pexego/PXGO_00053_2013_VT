from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # TODO: más tarde se usará para relacionar con la tarifa de coste
