##############################################################################
#
#    Copyright (C) 2017 Visiotech All Rights Reserved
#    $Jesus Garcia Manzanas <jgmanzanas@visiotechsecurity.com>$
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
import base64

# TODO: migrar parte del adapter
# @middleware
# class PickingExporter(Exporter):
#
#     _model_name = ['stock.picking']
#
#     def update(self, binding_id, mode):
#         picking = self.model.browse(binding_id)
#         report = self.env['report'].browse(picking.id)
#         result = report.get_pdf('stock.report_picking_custom')
#         result_encode = base64.b64encode(result)
#         name = picking.name.replace("\\", "/")
#         vals = {
#                 "odoo_id": picking.id,
#                 "name": name,
#                 "partner_id": picking.partner_id.commercial_partner_id.id,
#                 "date": picking.date,
#                 "date_done": picking.date_done or "",
#                 "move_type": picking.move_type,
#                 "carrier_name": picking.carrier_name or "",
#                 "carrier_tracking_ref": picking.carrier_tracking_ref or "",
#                 "origin": picking.origin,
#                 "state": picking.state,
#                 "pdf_file_data": result_encode or "",
#                 "dropship": picking.partner_id.dropship,
#                 }
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(binding_id, vals)
#
#     def delete(self, binding_id):
#         return self.backend_adapter.remove(binding_id)
#
# @middleware
# class PickingAdapter(GenericAdapter):
#     _model_name = 'stock.picking'
#     _middleware_model = 'picking'


class PickingListener(Component):
    _name = 'picking.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['stock.picking']

    def on_record_create(self, record, fields=None):
        picking = record
        if picking.partner_id.commercial_partner_id.web \
                and picking.partner_id.commercial_partner_id.active \
                and picking.picking_type_id.code == 'outgoing' \
                and not picking.not_sync \
                and picking.company_id.id == 1:
            record.with_delay(priority=1, eta=60).export_picking()

    def on_record_write(self, record, fields=None):
        picking = record
        up_fields = ["date_done", "move_type", "carrier_name", "carrier_tracking_ref",
                     "state", "not_sync", "company_id", "partner_id"]
        if picking.partner_id.commercial_partner_id.web \
                and picking.partner_id.commercial_partner_id.active \
                and picking.picking_type_id.code == 'outgoing' \
                and not picking.not_sync \
                and picking.company_id.id == 1:
            if 'name' in fields or 'partner_id' in fields or \
                    ('not_sync' in fields and not record.not_sync):
                record.with_delay(priority=1, eta=60).export_picking()
                picking_products = self.env['stock.move'].search([('picking_id', '=', picking.id)])
                for product in picking_products:
                    product.with_delay(priority=1, eta=120).export_pickingproduct()
            elif 'state' in fields and record.state == 'cancel' \
                    or 'not_sync' in fields and record.not_sync \
                    or 'company_id' in fields and record.company_id != 1:
                picking_products = self.env['stock.move'].search([('picking_id', '=', picking.id)])
                for product in picking_products:
                    product.with_delay(priority=1, eta=120).unlink_pickingproduct()
                record.with_delay(priority=5, eta=120).unlink_picking()
            else:
                for field in up_fields:
                    if field in fields:
                        record.with_delay(priority=2, eta=120).update_picking(fields=fields)
                        break
        else:
            job = self.env['queue.job'].sudo().search([('func_string', 'like', '%, ' + str(picking.id) + ')%'),
                                                       ('model_name', '=', model_name)], order='date_created desc',
                                                      limit=1)
            if job and 'unlink' not in job.name:
                record.with_delay(priority=5, eta=120).unlink_picking()

    def on_record_unlink(self, record):
        picking = record
        if picking.partner_id.commercial_partner_id.web \
                and picking.partner_id.commercial_partner_id.active \
                and picking.picking_type_id.code == 'outgoing' \
                and not picking.not_sync \
                and picking.company_id.id == 1:
            picking_products = self.env['stock.move'].search([('picking_id', '=', picking.id)])
            for product in picking_products:
                product.with_delay(priority=1, eta=120).unlink_pickingproduct()
            record.with_delay(priority=5, eta=120).unlink_picking()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_picking(self):
        # picking_exporter = _get_exporter(session, model_name, record_id,
        #                                  PickingExporter)
        # return picking_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_picking(self, fields):
        # picking_exporter = _get_exporter(session, model_name, record_id,
        #                                  PickingExporter)
        # return picking_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_picking(self):
        # picking_exporter = _get_exporter(session, model_name, record_id,
        #                                  PickingExporter)
        # return picking_exporter.delete(record_id)
        return True

# TODO: Migrar parte del adapter
# @middleware
# class PickingProductExporter(Exporter):
#
#     _model_name = ['stock.move']
#
#     def update(self, binding_id, mode):
#         picking_line = self.model.browse(binding_id)
#         vals = {
#             "odoo_id": picking_line.id,
#             "product_id": picking_line.product_id.id,
#             "product_qty": picking_line.product_uom_qty,
#             "picking_id": picking_line.picking_id.id
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
# class PickingProductAdapter(GenericAdapter):
#     _model_name = 'stock.move'
#     _middleware_model = 'pickingproduct'


class StockMoveListener(Component):
    _name = 'stock.move.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['stock.move']

    def on_record_create(self, record, fields=None):
        move_line = record
        if move_line.picking_id.partner_id.commercial_partner_id.web \
                and move_line.picking_id.partner_id.commercial_partner_id.active \
                and move_line.picking_id.picking_type_id.code == 'outgoing' \
                and not move_line.picking_id.not_sync \
                and move_line.picking_id.company_id.id == 1:
            record.with_delay(priority=1, eta=180).export_pickingproduct()

    def on_record_write(self, record, fields=None):
        up_fields = ["parent_id", "product_uom_qty", "product_id", "picking_id"]
        move_line = record
        if move_line.picking_id.partner_id.commercial_partner_id.web \
                and move_line.picking_id.partner_id.commercial_partner_id.active \
                and move_line.picking_id.picking_type_id.code == 'outgoing'\
                and not move_line.picking_id.not_sync \
                and move_line.picking_id.company_id.id == 1:
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=2, eta=240).update_pickingproduct(fields=fields)

    def on_record_unlink(self, record):
        move_line = record
        if move_line.picking_id.partner_id.commercial_partner_id.web \
                and move_line.picking_id.partner_id.commercial_partner_id.active \
                and move_line.picking_id.picking_type_id.code == 'outgoing' \
                and not move_line.picking_id.not_sync \
                and move_line.picking_id.company_id.id == 1:
            record.with_delay(priority=5, eta=240).unlink_pickingproduct()


class StockMove(models.Model):
    _inherit = 'stock.move'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_pickingproduct(self):
        # picking_product_exporter = _get_exporter(session, model_name, record_id,
        #                                          PickingProductExporter)
        # return picking_product_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_pickingproduct(self, fields):
        # picking_product_exporter = _get_exporter(session, model_name, record_id,
        #                                          PickingProductExporter)
        # return picking_product_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_pickingproduct(self):
        # picking_product_exporter = _get_exporter(session, model_name, record_id,
        #                                          PickingProductExporter)
        # return picking_product_exporter.delete(record_id)
        return True