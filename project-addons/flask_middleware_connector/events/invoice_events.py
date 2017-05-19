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
from openerp.addons.connector.event import on_record_create, on_record_write, \
    on_record_unlink
from openerp.addons.connector.queue.job import job
from .utils import _get_exporter
from ..backend import middleware
from openerp.addons.connector.unit.synchronizer import Exporter
from ..unit.backend_adapter import GenericAdapter


@middleware
class InvoiceExporter(Exporter):
    _model_name = ['account.invoice']

    def update(self, binding_id, mode):
        invoice = self.model.browse(binding_id)
        vals = {'odoo_id': invoice.id,
                'number': invoice.number,
                'partner_id': invoice.partner_id.commercial_partner_id.id,
                # 'partner_email_web': invoice.partner_id.email_web,
                'client_ref': invoice.name or "",
                'date_invoice': invoice.date_invoice,
                'date_due': invoice.date_due,
                'state': invoice.state,
                'subtotal_wt_rect': invoice.subtotal_wt_rect,
                'total_wt_rect': invoice.total_wt_rect}
        if mode == 'insert':
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class InvoiceAdapter(GenericAdapter):
    _model_name = 'account.invoice'
    _middleware_model = 'invoice'


@on_record_write(model_names='account.invoice')
def delay_write_invoice(session, model_name, record_id, vals):
    invoice = session.env[model_name].browse(record_id)
    up_fields = ["number", "client_ref", "date_invoice", "state", "partner_id",
                 "date_due", "subtotal_wt_rect", "subtotal_wt_rect"]

    if invoice.partner_id and invoice.partner_id.web:
        if vals.get('state', False) == 'open':
            export_invoice.delay(session, model_name, record_id)
        elif vals.get('state', False) == 'paid':
            update_invoice.delay(session, model_name, record_id)
        elif vals.get('state', False) == 'cancel':
            unlink_invoice(session, model_name, record_id)
        elif invoice.state == 'open':
            for field in up_fields:
                if field in vals:
                    update_invoice.delay(session, model_name, record_id)
                    break


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_invoice(session, model_name, record_id):
    invoice_exporter = _get_exporter(session, model_name, record_id, InvoiceExporter)
    return invoice_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_invoice(session, model_name, record_id):
    invoice_exporter = _get_exporter(session, model_name, record_id, InvoiceExporter)
    return invoice_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_invoice(session, model_name, record_id):
    invoice_exporter = _get_exporter(session, model_name, record_id, InvoiceExporter)
    return invoice_exporter.delete(record_id)
