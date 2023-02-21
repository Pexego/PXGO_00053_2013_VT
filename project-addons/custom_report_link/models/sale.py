# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def print_quotation(self):
        # no call to 'super' because it calls a removed report
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env.ref(
            'custom_report_link.action_report_saleorder').report_action(self)
