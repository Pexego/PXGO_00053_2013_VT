from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    battery_id = fields.Many2one('product.battery', 'Battery Type')
    num_batteries = fields.Float(string='Num. Batteries')

    battery_mode = fields.Selection(
        string='Battery Mode',
        selection=[('is_battery', 'Is Battery'),
                   ('contains_battery', 'Contains Battery'),
                   ('no_battery', 'No battery')])

    batt_origin = fields.Selection(
        string='Origin',
        selection=[('extra', 'Extra Community'),
                   ('intra', 'Intra Community'),
                   ('national', 'National')])

class ProductProduct(models.Model):
    _inherit = 'product.product'
    @api.onchange('battery_mode')
    def onchange_product_battery(self):
        if self.battery_mode not in ('contains_battery', 'is_battery'):
            self.num_batteries = '0'
            self.battery_id = None
