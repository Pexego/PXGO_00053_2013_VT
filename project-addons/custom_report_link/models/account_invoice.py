# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def invoice_print(self):
        super().invoice_print()
        return self.env.ref(
            'custom_report_link.action_report_invoice_custom').report_action(self)
