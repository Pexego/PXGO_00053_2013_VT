from odoo import api, fields, models, _, exceptions, tools
import base64
from datetime import datetime,timedelta
import xlsxwriter

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_eol_stock_move_domain(self, date):
        domain = super()._get_eol_stock_move_domain(date)
        dropship_route = self.env.ref('stock_dropshipping.picking_type_dropship')
        return domain + [('picking_id.picking_type_id', '!=', dropship_route.id)]
