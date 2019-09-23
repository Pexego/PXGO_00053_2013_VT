# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResPartner(models.Model):

    _inherit = "res.partner"

    automatice_purchases = fields.Boolean("Automatize purchases",
                                          help="Automatize the confirmation "
                                               "of purchases created from "
                                               "stock addons.")
