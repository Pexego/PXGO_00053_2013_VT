# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _write(self, vals):
        if vals.get('sale_id'):
            sale = self.env['sale.order'].browse(vals['sale_id'])
            if sale.not_sync:
                vals['not_sync'] = True
        return super()._write(vals)
