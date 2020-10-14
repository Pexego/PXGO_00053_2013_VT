# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class SaleStockReserve(models.TransientModel):
    _inherit = 'sale.stock.reserve'

    @api.multi
    def button_reserve(self):
        days_release_reserve = self.env['ir.config_parameter'].sudo().get_param('days_to_release_reserve_stock')
        now = datetime.now()
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
