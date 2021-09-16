# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class SaleStockReserve(models.TransientModel):
    _inherit = 'sale.stock.reserve'

    @api.multi
    def button_reserve(self):
        sale_line_id = self.env.context.get('active_id')
        sale_line_obj = self.env['sale.order.line'].browse(sale_line_id)
        order_obj = sale_line_obj.order_id
        days_release_reserve = self.env['ir.config_parameter'].sudo().get_param('days_to_release_reserve_stock')
        now = datetime.now()

        if order_obj.infinite_reservation:
            date_validity = (now + relativedelta(days=365)).strftime("%Y-%m-%d")
        else:
            date_validity = (now + relativedelta(days=int(days_release_reserve))).strftime("%Y-%m-%d")

        self.ensure_one()
        lines = self._get_so_lines()
        if lines and not self.date_validity \
                or self.date_validity > date_validity:
            lines.acquire_stock_reservation(date_validity=date_validity,
                                            note=self.note)
        else:
            super().button_reserve()
        return {'type': 'ir.actions.act_window_close'}
