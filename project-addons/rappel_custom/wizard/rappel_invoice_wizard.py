# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class ComputeRappelInvoice(models.TransientModel):

    _inherit = 'rappel.invoice.wzd'

    def action_invoice(self):
        res = super().action_invoice()
        compute_rappel_obj = self.env["rappel.calculated"]
        for rappel in compute_rappel_obj.browse(self.env.context["active_ids"]):
            if rappel.quantity <= 0:
                continue
            if rappel.invoice_id:
                invoice_rappel = rappel.invoice_id
                # Update description invoice lines
                for line in invoice_rappel.invoice_line:
                    line.write(
                        {'name': '{} ({}-{})'.format(
                            rappel.rappel_id.description,
                            rappel.date_start,
                            rappel.date_end)})
                # Update account data
                if not invoice_rappel.payment_mode_id \
                        or not invoice_rappel.partner_bank_id \
                        or not invoice_rappel.team_id:
                    partner_bank_id = False
                    for banks in rappel.partner_id.bank_ids:
                        for mandate in banks.mandate_ids:
                            if mandate.state == 'valid':
                                partner_bank_id = banks.id
                                break
                            else:
                                partner_bank_id = False
                    invoice_rappel.write(
                        {'payment_mode_id':
                         rappel.partner_id.customer_payment_mode.id,
                         'partner_bank_id': partner_bank_id,
                         'team_id': rappel.partner_id.team_id.id})
        return res
