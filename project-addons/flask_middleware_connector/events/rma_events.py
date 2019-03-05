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
# from .utils import _get_exporter
# from ..backend import middleware
# from openerp.addons.connector.unit.synchronizer import Exporter
# from ..unit.backend_adapter import GenericAdapter

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job
from odoo import models

import urllib2


# @middleware
# class RmaExporter(Exporter):
#
#     _model_name = ['crm.claim']
#
#     def update(self, binding_id, mode):
#         rma = self.model.browse(binding_id)
#         vals = {"odoo_id": rma.id,
#                 "date": rma.date,
#                 "date_received": rma.date_received,
#                 "delivery_type": rma.delivery_type,
#                 "stage_id": rma.stage_id.id,
#                 "partner_id": rma.partner_id.id,
#                 "number": rma.number,
#                 "last_update_date": rma.write_date,
#                 "delivery_address": rma.delivery_address_id.street,
#                 "delivery_zip": rma.delivery_address_id.zip,
#                 "delivery_city": rma.delivery_address_id.city,
#                 "delivery_state": rma.delivery_address_id.state_id.name,
#                 "delivery_country": rma.delivery_address_id.country_id.name,
#                 "type": rma.name}
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(binding_id, vals)
#
#     def delete(self, binding_id):
#         return self.backend_adapter.remove(binding_id)
#
#
# @middleware
# class RmaAdapter(GenericAdapter):
#     _model_name = 'crm.claim'
#     _middleware_model = 'rma'

class CrmClaimListener(Component):
    _name = 'claim.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['crm.claim']

    def on_record_create(self, record):
        if record.partner_id and record.partner_id.web:
            record.with_delay(priority=1).export_rma()

    def on_record_write(self, record, fields):
        rma = record
        up_fields = ["date", "date_received", "delivery_type", "delivery_address_id",
                     "partner_id", "stage_id", "number", "name"]
        job = self.env['queue.job'].sudo().search([('func_string', 'like', '%, ' + str(rma.id) + ')%'),
                                                      ('model_name', '=', model_name)], order='date_created desc', limit=1)
        if record.partner_id and rma.partner_id.web and ((job.name and 'unlink' in job.name) or not job.name):
            record.with_delay(priority=1).export_rma()
            for line in rma.claim_line_ids:
                line.with_delay(priority=10, eta=120).export_rmaproduct()
        elif 'partner_id' in fields and not record.partner_id or \
                record. partner_id and not rma.partner_id.web:
            record.with_delay(priority=6, eta=120).unlink_rma()
        elif rma.partner_id.web:
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=5, eta=120).update_rma(fields=fields)
                    break

    def on_record_unlink(self, record):
        if record.partner_id and record.partner_id.web:
            record.with_delay(priority=25, eta=120).unlink_rma()

class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rma(self):
        # rma_exporter = _get_exporter(session, model_name, record_id, RmaExporter)
        # return rma_exporter.update(record_id, "insert")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rma(self, fields):
        # rma_exporter = _get_exporter(session, model_name, record_id, RmaExporter)
        # return rma_exporter.update(record_id, "update")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rma(self):
        # rma_exporter = _get_exporter(session, model_name, record_id, RmaExporter)
        # return rma_exporter.delete(record_id)


# Lanzadores para lineas de reclamacion en lineas, reclamaciones y albaranes.

# @middleware
# class RmaProductExporter(Exporter):
#
#     _model_name = ['claim.line']
#
#     def update(self, binding_id, mode):
#         line = self.model.browse(binding_id)
#         vals = {
#             "odoo_id": line.id,
#             "id_rma": line.claim_id.id,
#             "reference": line.claim_id.number,
#             "name": line.name,
#             "move_out_customer_state": line.move_out_customer_state,
#             "internal_description": line.internal_description and
#             line.internal_description.replace("\n", " ") or '',
#             "product_returned_quantity": line.product_returned_quantity,
#             "product_id": line.product_id.id,
#             "equivalent_product_id": line.equivalent_product_id.id,
#             "entrance_date": line.date_in,
#             "end_date": line.date_out,
#             "status_id": line.substate_id.id,
#             "prodlot_id": line.prodlot_id.name,
#             "invoice_id": line.invoice_id.number,
#         }
#
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(binding_id, vals)
#
#     def delete(self, binding_id):
#         return self.backend_adapter.remove(binding_id)
#
#
# @middleware
# class RmaProductAdapter(GenericAdapter):
#     _model_name = 'claim.line'
#     _middleware_model = 'rmaproduct'

class ClaimLineListener(Component):
    _name = 'claim.line.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['claim.line']

    def on_record_create(self, record):
        if record.claim_id.partner_id.web and \
                (not record.equivalent_product_id) and \
                record.web:
            record.with_delay(priority=10, eta=120).export_rmaproduct()

    def on_record_write(self, record, fields=None):
        up_fields = ["product_id", "date_in", "date_out", "substate_id",
                     "name", "move_out_customer_state",
                     "internal_description", "product_returned_quantity",
                     "equivalent_product_id", "prodlot_id", "invoice_id"]
        if record.web:
            record.with_delay(priority=10, eta=120).export_rmaproduct()
        elif not record.web:
            record.with_delay(priority=20, eta=180).unlink_rmaproduct()
        elif record.claim_id.partner_id.web and record.web:
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=15, eta=180).update_rmaproduct(fields=fields)
                    break

    def on_record_unlink(self, record):
        if record.claim_id.partner_id.web and record.web:
            record.with_delay(priority=20, eta=180).unlink_rmaproduct()

class ClaimLine(models.Model):
    _inherit = 'claim.line'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rmaproduct(self):
        # rmaproduct_exporter = _get_exporter(session, model_name, record_id,
        #                                     RmaProductExporter)
        # return rmaproduct_exporter.update(record_id, "insert")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rmaproduct(self, fields):
        # rmaproduct_exporter = _get_exporter(session, model_name, record_id,
        #                                     RmaProductExporter)
        # return rmaproduct_exporter.update(record_id, "update")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rmaproduct(self):
        # rmaproduct_exporter = _get_exporter(session, model_name, record_id,
        #                                     RmaProductExporter)
        # return rmaproduct_exporter.delete(record_id)



# @middleware
# class RmaStatusExporter(Exporter):
#
#     _model_name = ['substate.substate']
#
#     def update(self, binding_id, mode):
#         line = self.model.browse(binding_id)
#         vals = {
#             "odoo_id": line.id,
#             "name": line.name
#         }
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(binding_id, vals)
#
#     def delete(self, binding_id):
#         return self.backend_adapter.remove(binding_id)
#
#
# @middleware
# class RmaStatusAdapter(GenericAdapter):
#     _model_name = 'substate.substate'
#     _middleware_model = 'rmastatus'

class SubstateListener(Component):
    _name = 'substate.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['substate.substate']

    def on_record_create(self, record):
        record.with_delay(priority=1).export_rma_status()

    def on_record_write(self, record, fields=None):
        up_fields = ["name"]
        for field in up_fields:
            if field in fields:
                record.with_delay(priority=2).update_rma_status(fields=fields)
                break

    def on_record_unlink(self, record):
        record.with_delay(priority=100).unlink_rma_status()


class SubstateSubstate(models.Model):
    _inherit = 'substate.substate'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rma_status(self):
        # rma_status_exporter = _get_exporter(session, model_name, record_id,
        #                                     RmaStatusExporter)
        # return rma_status_exporter.update(record_id, "insert")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rma_status(self, fields):
        # rma_status_exporter = _get_exporter(session, model_name, record_id,
        #                                     RmaStatusExporter)
        # return rma_status_exporter.update(record_id, "update")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rma_status(self):
        # rma_status_exporter = _get_exporter(session, model_name, record_id,
        #                                     RmaStatusExporter)
        # return rma_status_exporter.delete(record_id)


# @middleware
# class RmaStageExporter(Exporter):
#
#     _model_name = ['crm.claim.stage']
#
#     def update(self, binding_id, mode):
#         line = self.model.browse(binding_id)
#         vals = {
#             "odoo_id": line.id,
#             "name": line.name
#         }
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(binding_id, vals)
#
#     def delete(self, binding_id):
#         return self.backend_adapter.remove(binding_id)
#
#
# @middleware
# class RmaStageAdapter(GenericAdapter):
#     _model_name = 'crm.claim.stage'
#     _middleware_model = 'rmastage'


class ClaimStageListener(Component):
    _name = 'claim.stage.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['crm.claim.stage']

    def on_record_create(self, record):
        record.with_delay(priority=1).export_rma_stage()

    def on_record_write(self, record, fields=None):
        up_fields = ["name"]
        for field in up_fields:
            if field in fields:
                record.with_delay(priority=2).update_rma_stage(fields=fields)
                break

    def on_record_unlink(self, record):
        record.with_delay(priority=100).unlink_rma_stage()

class CrmClaimStage(models.Model):
    _inherit = 'crm.claim.stage'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_rma_stage(session, model_name, record_id):
        # rma_stage_exporter = _get_exporter(session, model_name, record_id,
        #                                     RmaStageExporter)
        # return rma_stage_exporter.update(record_id, "insert")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_rma_stage(session, model_name, record_id):
        # rma_stage_exporter = _get_exporter(session, model_name, record_id,
        #                                     RmaStageExporter)
        # return rma_stage_exporter.update(record_id, "update")


    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_rma_stage(session, model_name, record_id):
        # rma_stage_exporter = _get_exporter(session, model_name, record_id,
        #                                     RmaStageExporter)
        # return rma_stage_exporter.delete(record_id)
