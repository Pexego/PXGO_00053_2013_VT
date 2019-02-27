# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import exceptions, models, _


class SaleAdvancePaymentInv(models.TransientModel):

    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(
            self._context.get('active_ids', []))
        for order in sale_orders:
            # Compruebo la empresa actual y su padre...
            for partner in order.partner_id.get_partners_to_check():
                if partner.blocked_sales and not order.allow_confirm_blocked:
                    title = _("Warning for %s") % partner.name
                    message = _('Customer blocked by lack of payment. \
                        Check the maturity dates of their account move lines.')
                    raise exceptions.UserError(title, message)
        return super().create_invoices()
