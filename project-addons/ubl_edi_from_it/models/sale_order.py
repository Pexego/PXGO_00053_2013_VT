# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class SaleOrder(models.Model):

    _inherit = "sale.order"

    not_sync = fields.Boolean("Not sync", copy=False, readonly=True,
                              help="Delivery pickings from this order "
                                   "not will be synced with vstock")
