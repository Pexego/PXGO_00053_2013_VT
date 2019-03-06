##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# from .utils import _get_exporter
# from ..backend import middleware
# from openerp.addons.connector.unit.synchronizer import Exporter
# from ..unit.backend_adapter import GenericAdapter

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job
from odoo import models


# TODO: Migrar parte del adapter
# @middleware
# class InvoiceExporter(Exporter):
#     _model_name = ['account.invoice']
#
#     def update(self, binding_id, mode):
#         invoice = self.model.browse(binding_id)
#         report = self.env['report'].browse(invoice.id)
#         result = report.get_pdf('account.report_invoice_custom')
#         result_encode = base64.b64encode(result)
#         if not invoice.state_web:
#             invoice._get_state_web()
#
#         vals = {'odoo_id': invoice.id,
#                 'number': invoice.number,
#                 'partner_id': invoice.partner_id.commercial_partner_id.id,
#                 'client_ref': invoice.name or "",
#                 'date_invoice': invoice.date_invoice,
#                 'date_due': invoice.date_due,
#                 'subtotal_wt_rect': invoice.amount_untaxed_signed,
#                 'total_wt_rect': invoice.amount_total_signed,
#                 'pdf_file_data': result_encode,
#                 'state': invoice.state_web, #Llamada a _get_state_web para evitar problemas en facturas que no tienen inicializado ese valor
#                 'payment_mode_id': invoice.payment_mode_id.name,
#                 'orders': invoice.orders}
#         if mode == 'insert':
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(binding_id, vals)
#
#     def delete(self, binding_id):
#         return self.backend_adapter.remove(binding_id)
#
#
# @middleware
# class InvoiceAdapter(GenericAdapter):
#     _model_name = 'account.invoice'
#     _middleware_model = 'invoice'


class InvoiceListener(Component):
    _name = 'invoice.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['account.invoice']

    def on_record_write(self, record, fields=None):
        invoice = record
        model_name = 'account.invoice'
        up_fields = ["number", "client_ref", "date_invoice", "state_web", "partner_id", "state",
                     "date_due", "amount_untaxed_signed", "amount_total_signed", "payment_ids", "payment_mode_id"]
        if invoice.partner_id and invoice.commercial_partner_id.web and invoice.company_id.id == 1:
            if 'state' in fields or 'state_web' in fields:
                job = self.env['queue.job'].sudo().search([('func_string', 'not like', '%confirm_one_invoice%'),
                                                          ('func_string', 'like', '%, ' + str(invoice.id) + ')%'),
                                                          ('model_name', '=', model_name)], order='date_created desc',
                                                          limit=1)
                if job:
                    if invoice.state_web == 'open' and 'unlink_invoice' in job[0].func_string:
                        record.with_delay(priority=5, eta=120).export_invoice()
                    elif invoice.state_web in ('paid', 'returned', 'remitted'):
                        record.with_delay(priority=10, eta=120).update_invoice(fields=fields)
                    elif invoice.state_web == 'cancel' and 'unlink_invoice' not in job[0].func_string:
                        record.with_delay(priority=15, eta=120).unlink_invoice()
                    elif invoice.state_web == 'open':
                        for field in up_fields:
                            if field in fields:
                                record.with_delay(priority=10, eta=120).update_invoice(fields=fields)
                                break
                elif invoice.state_web == 'open':
                    record.with_delay(priority=5, eta=120).export_invoice()
            elif invoice.state in ('open', 'paid'):
                for field in up_fields:
                    if field in fields:
                        record.with_delay(priority=10, eta=60).update_invoice(fields=fields)
                        break


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_invoice(self):
        # invoice_exporter = _get_exporter(session, model_name, record_id, InvoiceExporter)
        # return invoice_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_invoice(self, fields):
        # invoice_exporter = _get_exporter(session, model_name, record_id, InvoiceExporter)
        # return invoice_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_invoice(self):
        # invoice_exporter = _get_exporter(session, model_name, record_id, InvoiceExporter)
        # return invoice_exporter.delete(record_id)
        return True
