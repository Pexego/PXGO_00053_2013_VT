# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    force_location = fields.\
        Boolean("Force location",
                help="Force orig. location on picking creation")
