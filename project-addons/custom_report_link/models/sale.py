# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def print_quotation(self):
        super().print_quotation()
        return self.env.ref(
            'custom_report_link.action_report_saleorder').report_action(self)
