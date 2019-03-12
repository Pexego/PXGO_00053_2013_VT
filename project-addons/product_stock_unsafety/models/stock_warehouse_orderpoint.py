# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    min_days_id = fields.Many2one('minimum.day',
                                  'Stock Mínimum Days',
                                  required=True)
