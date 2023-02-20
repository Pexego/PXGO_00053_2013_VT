# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def do_print_picking(self):
        # no call to 'super' because it calls a removed report
        self.write({'printed': True})
        return self.env.ref('custom_report_link.report_picking_custom_action').report_action(self)
