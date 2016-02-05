# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from .connector import get_environment
from .backend import middleware
from openerp.addons.connector.unit.synchronizer import Exporter
from .unit.backend_adapter import GenericAdapter
from openerp.addons.connector.event import Event


@middleware
class RmaExporter(Exporter):

    _model_name = ['crm.claim']

    def update(self, binding_id, mode):
        rma = self.model.browse(binding_id)
        vals = {"odoo_id": rma.id,
                "partner_id": rma.partner_id.id}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class RmaAdapter(GenericAdapter):
    _model_name = 'crm.claim'
    _middleware_model = 'rma'


@on_record_create(model_names='crm.claim')
def delay_create_rma(session, model_name, record_id, vals):
    rma = session.env[model_name].browse(record_id)
    if rma.partner_id and rma.partner_id.web:
        export_rma(session, model_name, record_id)


@on_record_write(model_names='crm.claim')
def delay_write_rma(session, model_name, record_id, vals):
    rma = session.env[model_name].browse(record_id)
    up_fields = ["partner_id"]
    if vals.get("partner_id", False) and rma.partner_id.web:
        export_rma(session, model_name, record_id)
    elif 'partner_id' in vals.keys() and not vals.get("partner_id"):
        unlink_rma(session, model_name, record_id)
    elif rma.partner_id.web:
        for field in up_fields:
            if field in vals:
                update_rma.delay(session, model_name, record_id)
                break


@on_record_unlink(model_names='crm.claim')
def delay_unlink_rma(session, model_name, record_id):
    rma = session.env[model_name].browse(record_id)
    if rma.partner_id and rma.partner_id.web:
        unlink_rma.delay(session, model_name, record_id)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_rma(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    rma_exporter = env.get_connector_unit(RmaExporter)
    return rma_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_rma(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    rma_exporter = env.get_connector_unit(RmaExporter)
    return rma_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_rma(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    rma_exporter = env.get_connector_unit(RmaExporter)
    return rma_exporter.delete(record_id)


# Lanzadores para lineas de reclamacion en lineas, reclamaciones y albaranes.

@middleware
class RmaProductExporter(Exporter):

    _model_name = ['claim.line']

    def update(self, binding_id, mode):
        line = self.model.browse(binding_id)
        vals = {
            "odoo_id": line.id,
            "id_rma": line.claim_id.id,
            "reference": line.claim_id.number,
            "product_id": line.product_id.id,
            "entrance_date": line.date_in,
            "end_date": line.date_out,
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class RmaProductAdapter(GenericAdapter):
    _model_name = 'claim.line'
    _middleware_model = 'rmaproduct'


@on_record_create(model_names='claim.line')
def delay_create_rma_line(session, model_name, record_id, vals):
    claim_line = session.env[model_name].browse(record_id)
    if claim_line.claim_id.partner_id.web and \
            claim_line.product_id.web == 'published':
        export_rmaproduct.delay(session, model_name, record_id)


@on_record_write(model_names='claim.line')
def delay_write_rma_line(session, model_name, record_id, vals):

    claim_line = session.env[model_name].browse(record_id)
    up_fields = ["product_id", "date_in", "date_out"]
    if claim_line.claim_id.partner_id.web and \
            claim_line.product_id.web == 'published':
        for field in up_fields:
            if field in vals:
                update_rmaproduct.delay(session, model_name, record_id)
                break


@on_record_unlink(model_names='claim.line')
def delay_unlink_rma_line(session, model_name, record_id):
    claim_line = session.env[model_name].browse(record_id)
    if claim_line.claim_id.partner_id.web and \
            claim_line.product_id.web == 'published':
        unlink_rmaproduct.delay(session, model_name, record_id)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_rmaproduct(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    rmaproduct_exporter = env.get_connector_unit(RmaProductExporter)
    return rmaproduct_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_rmaproduct(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    rmaproduct_exporter = env.get_connector_unit(RmaProductExporter)
    return rmaproduct_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_rmaproduct(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    rmaproduct_exporter = env.get_connector_unit(RmaProductExporter)
    return rmaproduct_exporter.delete(record_id)
