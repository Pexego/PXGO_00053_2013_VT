# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class MrpCustomizeType(models.Model):

    _name = 'mrp.customize.type'

    name = fields.Char(required=True)
    code = fields.Integer(required=True)
    aux_product = fields.Boolean('Needs another product')
