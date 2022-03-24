from odoo import fields, models


class ProductBattery(models.Model):

    _name = 'product.battery'

    name = fields.Char("Battery type", size=64, required=True)
    notes = fields.Text('Notes')
    forbidden_ship_ids = fields.Many2many('transportation.service', string='Forbidden shipping services')