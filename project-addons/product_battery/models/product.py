from odoo import fields, models


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    battery_id = fields.Many2one('product.battery', 'Battery Type')
    num_batteries = fields.Float(string='Num. Batteries')

    battery_mode = fields.Selection(
        string='Battery Mode',
        selection=[('is_battery', 'Is Battery'),
                   ('contains_battery', 'Contains Battery')])

    batt_origin = fields.Selection(
        string='Origin',
        selection=[('extra', 'Extra Community'),
                   ('intra', 'Intra Community'),
                   ('national', 'National')])
