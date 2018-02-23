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
from .utils import _get_exporter
from ..backend import middleware
from openerp.addons.connector.unit.synchronizer import Exporter
from ..unit.backend_adapter import GenericAdapter
from openerp.addons.connector.event import Event
import urllib2


@middleware
class RmaExporter(Exporter):

    _model_name = ['crm.claim']

    def update(self, binding_id, mode):
        rma = self.model.browse(binding_id)
        vals = {"odoo_id": rma.id,
                "date": rma.date,
                "date_received": rma.date_received,
                "delivery_type": rma.delivery_type,
                "stage_id": rma.stage_id.id,
                "partner_id": rma.partner_id.id,
                "number": rma.number,
                "last_update_date": rma.write_date,
                "delivery_address": rma.delivery_address_id.street,
                "delivery_zip": rma.delivery_address_id.zip,
                "delivery_city": rma.delivery_address_id.city,
                "delivery_state": rma.delivery_address_id.state_id.name,
                "delivery_country": rma.delivery_address_id.country_id.name,
                "type": rma.name}
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
        export_rma.delay(session, model_name, record_id, priority=1)


@on_record_write(model_names='crm.claim')
def delay_write_rma(session, model_name, record_id, vals):
    rma = session.env[model_name].browse(record_id)
    up_fields = ["date", "date_received", "delivery_type", "delivery_address_id",
                 "partner_id", "stage_id", "number", "name"]
    job = session.env['queue.job'].search([('func_string', 'like', '%, ' + str(rma.id) + ')%'),
                                           ('model_name', '=', model_name)], order='date_created desc', limit=1)
    if vals.get("partner_id", False) and rma.partner_id.web and job.name and 'unlink' in job.name:
        export_rma.delay(session, model_name, record_id, priority=1)
        for line in rma.claim_line_ids:
            export_rmaproduct.delay(session, 'claim.line', line.id, priority=10, eta=120)
    elif 'partner_id' in vals.keys() and not vals.get("partner_id") or \
            vals.get("partner_id", False) and not rma.partner_id.web:
        unlink_rma.delay(session, model_name, record_id, priority=6, eta=120)
    elif rma.partner_id.web:
        for field in up_fields:
            if field in vals:
                update_rma.delay(session, model_name, record_id, priority=5, eta=120)
                break


@on_record_unlink(model_names='crm.claim')
def delay_unlink_rma(session, model_name, record_id):
    rma = session.env[model_name].browse(record_id)
    if rma.partner_id and rma.partner_id.web:
        unlink_rma.delay(session, model_name, record_id, priority=25, eta=120)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_rma(session, model_name, record_id):
    rma_exporter = _get_exporter(session, model_name, record_id, RmaExporter)
    return rma_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_rma(session, model_name, record_id):
    rma_exporter = _get_exporter(session, model_name, record_id, RmaExporter)
    return rma_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_rma(session, model_name, record_id):
    rma_exporter = _get_exporter(session, model_name, record_id, RmaExporter)
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
            "name": line.name,
            "move_out_customer_state": line.move_out_customer_state,
            "internal_description": line.internal_description and
            line.internal_description.replace("\n", " ") or '',
            "product_returned_quantity": line.product_returned_quantity,
            "product_id": line.product_id.id,
            "equivalent_product_id": line.equivalent_product_id.id,
            "entrance_date": line.date_in,
            "end_date": line.date_out,
            "status_id": line.substate_id.id,
            "prodlot_id": line.prodlot_id.name,
            "invoice_id": line.invoice_id.number,
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
            (not claim_line.equivalent_product_id) and \
            vals.get('web', False):
        export_rmaproduct.delay(session, model_name, record_id, priority=10, eta=120)


@on_record_write(model_names='claim.line')
def delay_write_rma_line(session, model_name, record_id, vals):
    claim_line = session.env[model_name].browse(record_id)

    up_fields = ["product_id", "date_in", "date_out", "substate_id",
                 "name", "move_out_customer_state",
                 "internal_description", "product_returned_quantity",
                 "equivalent_product_id", "prodlot_id", "invoice_id"]
    if vals.get('web', False):
        export_rmaproduct.delay(session, model_name, record_id, priority=10, eta=120)
    elif not vals.get('web', False) and not claim_line.web:
        unlink_rmaproduct.delay(session, model_name, record_id, priority=20, eta=180)
    elif claim_line.claim_id.partner_id.web and claim_line.web:
        for field in up_fields:
            if field in vals:
                update_rmaproduct.delay(session, model_name, record_id,
                                        priority=15, eta=180)
                break


@on_record_unlink(model_names='claim.line')
def delay_unlink_rma_line(session, model_name, record_id):
    claim_line = session.env[model_name].browse(record_id)
    if claim_line.claim_id.partner_id.web and claim_line.web:
        unlink_rmaproduct.delay(session, model_name, record_id, priority=20, eta=180)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_rmaproduct(session, model_name, record_id):
    rmaproduct_exporter = _get_exporter(session, model_name, record_id,
                                        RmaProductExporter)
    return rmaproduct_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_rmaproduct(session, model_name, record_id):
    rmaproduct_exporter = _get_exporter(session, model_name, record_id,
                                        RmaProductExporter)
    return rmaproduct_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_rmaproduct(session, model_name, record_id):
    rmaproduct_exporter = _get_exporter(session, model_name, record_id,
                                        RmaProductExporter)
    return rmaproduct_exporter.delete(record_id)



@middleware
class RmaStatusExporter(Exporter):

    _model_name = ['substate.substate']

    def update(self, binding_id, mode):
        line = self.model.browse(binding_id)
        vals = {
            "odoo_id": line.id,
            "name": line.name
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class RmaStatusAdapter(GenericAdapter):
    _model_name = 'substate.substate'
    _middleware_model = 'rmastatus'


@on_record_create(model_names='substate.substate')
def delay_create_rmastatus(session, model_name, record_id, vals):
    substate = session.env[model_name].browse(record_id)
    export_rma_status.delay(session, model_name, record_id, priority=1)


@on_record_write(model_names='substate.substate')
def delay_write_rmastatus(session, model_name, record_id, vals):

    substate = session.env[model_name].browse(record_id)
    up_fields = ["name"]
    for field in up_fields:
        if field in vals:
            update_rma_status.delay(session, model_name, record_id, priority=2)
            break


@on_record_unlink(model_names='substate.substate')
def delay_unlink_rmastatus(session, model_name, record_id):
    substate = session.env[model_name].browse(record_id)
    unlink_rma_status.delay(session, model_name, record_id, priority=100)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_rma_status(session, model_name, record_id):
    rma_status_exporter = _get_exporter(session, model_name, record_id,
                                        RmaStatusExporter)
    return rma_status_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_rma_status(session, model_name, record_id):
    rma_status_exporter = _get_exporter(session, model_name, record_id,
                                        RmaStatusExporter)
    return rma_status_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_rma_status(session, model_name, record_id):
    rma_status_exporter = _get_exporter(session, model_name, record_id,
                                        RmaStatusExporter)
    return rma_status_exporter.delete(record_id)


@middleware
class RmaStageExporter(Exporter):

    _model_name = ['crm.claim.stage']

    def update(self, binding_id, mode):
        line = self.model.browse(binding_id)
        vals = {
            "odoo_id": line.id,
            "name": line.name
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class RmaStageAdapter(GenericAdapter):
    _model_name = 'crm.claim.stage'
    _middleware_model = 'rmastage'


@on_record_create(model_names='crm.claim.stage')
def delay_create_rmastage(session, model_name, record_id, vals):
    stage = session.env[model_name].browse(record_id)
    export_rma_stage.delay(session, model_name, record_id, priority=1)


@on_record_write(model_names='crm.claim.stage')
def delay_write_rmastage(session, model_name, record_id, vals):

    stage = session.env[model_name].browse(record_id)
    up_fields = ["name"]
    for field in up_fields:
        if field in vals:
            update_rma_stage.delay(session, model_name, record_id, priority=2)
            break


@on_record_unlink(model_names='crm.claim.stage')
def delay_unlink_rmastage(session, model_name, record_id):
    stage = session.env[model_name].browse(record_id)
    unlink_rma_stage.delay(session, model_name, record_id, priority=100)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_rma_stage(session, model_name, record_id):
    rma_stage_exporter = _get_exporter(session, model_name, record_id,
                                        RmaStageExporter)
    return rma_stage_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_rma_stage(session, model_name, record_id):
    rma_stage_exporter = _get_exporter(session, model_name, record_id,
                                        RmaStageExporter)
    return rma_stage_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_rma_stage(session, model_name, record_id):
    rma_stage_exporter = _get_exporter(session, model_name, record_id,
                                        RmaStageExporter)
    return rma_stage_exporter.delete(record_id)
