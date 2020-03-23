# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from datetime import datetime


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
                invoice_rappel.compute_taxes()
                partner = rappel.partner_id
                # Update description invoice lines
                for line in invoice_rappel.invoice_line_ids:
                    ctx = dict(rappel.rappel_id._context or {})
                    ctx['lang'] = partner.lang
                    line.write(
                        {'name': '{} ({} - {})'.format(
                            rappel.rappel_id.with_context(ctx).description,
                            datetime.strptime(rappel.date_start, "%Y-%m-%d").strftime('%d/%m/%Y'),
                            datetime.strptime(rappel.date_end, "%Y-%m-%d").strftime('%d/%m/%Y'))})
                # Update account data
                if not invoice_rappel.payment_mode_id \
                        or not invoice_rappel.mandate_id \
                        or not invoice_rappel.team_id:
                    invoice_rappel.write(
                        {'payment_mode_id':
                         partner.customer_payment_mode_id.id,
                         'payment_term_id': partner.property_payment_term_id.id,
                         'mandate_id': partner.valid_mandate_id.id,
                         'team_id': partner.team_id.id})
        return res
