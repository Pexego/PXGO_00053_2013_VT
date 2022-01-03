from odoo import fields, models, api

class OrderpointTemplate(models.Model):
    _inherit = 'stock.warehouse.orderpoint.template'
    all_products = fields.Boolean()
