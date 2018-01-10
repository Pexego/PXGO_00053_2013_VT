# -*- coding: utf-8 -*-
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
from openerp import models
from openerp.addons.connector.event import on_record_create, on_record_write, \
    on_record_unlink
from openerp.addons.connector.queue.job import job
from .utils import _get_exporter
from ..backend import middleware
from openerp.addons.connector.unit.synchronizer import Exporter
from ..unit.backend_adapter import GenericAdapter
import xmlrpclib

import base64


@middleware
class InvoiceExporter(Exporter):
    _model_name = ['account.invoice']

    def update(self, binding_id, mode, state=None):
        invoice = self.model.browse(binding_id)
        report = self.env['report'].browse(invoice.id)
        result = report.get_pdf('account.report_invoice_custom')
        result_encode = base64.b64encode(result)
        vals = {'odoo_id': invoice.id,
                'number': invoice.number,
                'partner_id': invoice.partner_id.commercial_partner_id.id,
                'client_ref': invoice.name or "",
                'date_invoice': invoice.date_invoice,
                'date_due': invoice.date_due,
                'subtotal_wt_rect': invoice.subtotal_wt_rect,
                'total_wt_rect': invoice.total_wt_rect,
                'pdf_file_data': result_encode,
                'payment_mode_id': invoice.payment_mode_id.name}
        if state:
            vals['state'] = state
        else:
            vals['state'] = invoice.state
            res = _new_state_invoice(invoice, vals)
            if res:
                vals['state'] = res
        if mode == 'insert':
            if invoice.returned_payment and invoice.state == 'open':
                vals['state'] = 'returned'
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class InvoiceAdapter(GenericAdapter):
    _model_name = 'account.invoice'
    _middleware_model = 'invoice'


def _new_state_invoice(invoice, vals):
    res = None
    if 'payment_mode_id' in vals and vals.get('payment_mode_id', False) == 'Recibo domicialiado' \
            or invoice.payment_mode_id.name == 'Recibo domiciliado':
        if 'returned_payment' in vals and vals.get('returned_payment', False) or invoice.returned_payment:
            if 'state' in vals and vals.get('state', False) == 'open' and \
                    invoice.returned_payment or ('returned_payment' in vals and vals.get('returned_payment', False)):
                res = 'returned'
        elif 'state' in vals and vals.get('state', False) == 'paid':
            for payment in invoice.payment_ids:
                for payment_account in payment.move_id.line_id:
                    if payment_account.account_id.code == '43120000' \
                                        and payment_account.account_id.user_type.code == 'receivable' \
                                        and payment_account.reconcile_id:
                        for reconcile_line in payment_account.reconcile_id.line_id:
                            if reconcile_line.move_id != payment.move_id and reconcile_line.credit != 0:
                                res = 'paid'
                        break
                    else:
                        res = 'remitted'
                if res == 'paid':
                    break
    return res


@on_record_write(model_names='account.invoice')
def delay_write_invoice(session, model_name, record_id, vals, checked_state=False):
    invoice = session.env[model_name].browse(record_id)
    up_fields = ["number", "client_ref", "date_invoice", "state", "partner_id",
                 "date_due", "subtotal_wt_rect", "subtotal_wt_rect", "payment_ids",
                 "returned_payment", "payment_mode_id"]

    if invoice.partner_id and invoice.commercial_partner_id.web:
        job = session.env['queue.job'].search([('func_string', 'not like', '%confirm_one_invoice%'),
                                               ('func_string', 'like', '%, ' + str(invoice.id) + ')%'),
                                               ('model_name', '=', model_name)], order='date_created desc', limit=1)
        if job:
            if not checked_state:
                vals['state'] = _new_state_invoice(invoice, vals)
                if not vals['state']:
                    del vals['state']
            if vals.get('state', False) == 'open' and 'unlink_invoice' in job[0].func_string:
                export_invoice.delay(session, model_name, record_id, priority=5)
            elif vals.get('state', False) in ('paid', 'returned', 'remitted'):
                update_invoice.delay(session, model_name, record_id, state=vals.get('state', False),
                                     priority=10, eta=60)
            elif vals.get('state', False) == 'cancel' and 'unlink_invoice' not in job[0].func_string:
                unlink_invoice.delay(session, model_name, record_id, priority=15)
            elif invoice.state == 'open':
                for field in up_fields:
                    if field in vals:
                        update_invoice.delay(session, model_name, record_id, priority=10, eta=60)
                        break
        elif invoice.state == 'open':
            export_invoice.delay(session, model_name, record_id, priority=5, eta=60)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_invoice(session, model_name, record_id):
    invoice_exporter = _get_exporter(session, model_name, record_id, InvoiceExporter)
    return invoice_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_invoice(session, model_name, record_id, state=None):
    invoice_exporter = _get_exporter(session, model_name, record_id, InvoiceExporter)
    return invoice_exporter.update(record_id, "update", state)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_invoice(session, model_name, record_id):
    invoice_exporter = _get_exporter(session, model_name, record_id, InvoiceExporter)
    return invoice_exporter.delete(record_id)
