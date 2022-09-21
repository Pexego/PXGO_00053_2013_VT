from odoo import models, fields, _, exceptions, api


class KitchenCustomization(models.Model):
    _name = 'customization.type'

    name = fields.Char('Name')

    rule_ids = fields.One2many('automatic.customization.type.rule','type_id')

    preview = fields.Boolean()
