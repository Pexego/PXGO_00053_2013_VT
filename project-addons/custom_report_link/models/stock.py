# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def do_print_picking(self):
        super().do_print_picking()
        return self.env.ref('stock.report_picking_custom').report_action(self)
