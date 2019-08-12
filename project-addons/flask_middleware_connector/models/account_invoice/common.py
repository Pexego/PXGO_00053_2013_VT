# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job
from odoo import api, fields, models


class InvoiceListener(Component):
    _name = 'invoice.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['account.invoice']

    def on_record_write(self, record, fields=None):
        invoice = record
        up_fields = ["number", "client_ref", "date_invoice", "state_web", "partner_id", "state",
                     "date_due", "amount_untaxed_signed", "amount_total_signed", "payment_ids", "payment_mode_id"]

        if invoice.partner_id and invoice.commercial_partner_id.web and invoice.company_id.id == 1:
            if 'state' in fields or 'state_web' in fields:
                if invoice.state_web == 'open' and not invoice.in_web:
                    invoice.in_web = True
                    record.with_delay(priority=5, eta=120).export_invoice()
                elif invoice.state_web in ('paid', 'returned', 'remitted'):
                    record.with_delay(priority=10, eta=120).update_invoice(fields=fields)
                elif invoice.state_web == 'cancel' and invoice.in_web:
                    invoice.in_web = False
                    record.with_delay(priority=15, eta=120).unlink_invoice()
                elif invoice.state_web == 'open':
                    for field in up_fields:
                        if field in fields:
                            record.with_delay(priority=10, eta=120).update_invoice(fields=fields)
                            break
            elif invoice.state in ('open', 'paid'):
                for field in up_fields:
                    if field in fields:
                        record.with_delay(priority=10, eta=60).update_invoice(fields=fields)
                        break


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    orders = fields.Char(compute='_compute_orders', readonly=True, store=False)
    # This field is used to check if the object has been sent to the web or not
    in_web = fields.Boolean(default=False)

    @api.multi
    def _compute_orders(self):
        for invoice in self:
            orders = ''
            for order in invoice.sale_order_ids:
                orders += order.name + ','
            if orders.endswith(','):
                self.orders = orders[:-1]

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_invoice(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'insert')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_invoice(self, fields):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.update(self, 'update')
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_invoice(self):
        backend = self.env["middleware.backend"].search([])[0]
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.delete(self)
        return True
