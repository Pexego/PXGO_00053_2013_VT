# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResPartner(models.Model):

    _inherit = 'res.partner'

    attach_ubl_xml_file = fields.Boolean("Attach UBL XML File")
