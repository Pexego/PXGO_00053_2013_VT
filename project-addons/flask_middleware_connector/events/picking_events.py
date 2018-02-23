# -*- coding: utf-8 -*-
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
from openerp.addons.connector.event import on_record_create, on_record_write, \
    on_record_unlink
from openerp.addons.connector.queue.job import job
from .utils import _get_exporter
from ..backend import middleware
from openerp.addons.connector.unit.synchronizer import Exporter
from ..unit.backend_adapter import GenericAdapter
import base64


@middleware
class PickingExporter(Exporter):

    _model_name = ['stock.picking']

    def update(self, binding_id, mode):
        picking = self.model.browse(binding_id)
        report = self.env['report'].browse(picking.id)
        result = report.get_pdf('stock.report_picking_custom')
        result_encode = base64.b64encode(result)
        name = picking.name.replace("\\", "/")
        vals = {
                "odoo_id": picking.id,
                "name": name,
                "partner_id": picking.partner_id.commercial_partner_id.id,
                "date": picking.date,
                "date_done": picking.date_done or "",
                "move_type": picking.move_type,
                "carrier_name": picking.carrier_name or "",
                "carrier_tracking_ref": picking.carrier_tracking_ref or "",
                "origin": picking.origin,
                "state": picking.state,
                "pdf_file_data": result_encode or "",
                "dropship": picking.partner_id.dropship,
                }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)

@middleware
class PickingAdapter(GenericAdapter):
    _model_name = 'stock.picking'
    _middleware_model = 'picking'


@on_record_create(model_names='stock.picking')
def delay_export_picking_create(session, model_name, record_id, vals):
    picking = session.env[model_name].browse(record_id)
    if picking.partner_id.commercial_partner_id.web \
            and picking.partner_id.commercial_partner_id.active \
            and picking.picking_type_id.code == 'outgoing' \
            and not picking.not_sync \
            and picking.company_id.id == 1:
        export_picking.delay(session, model_name, record_id, priority=1, eta=60)


@on_record_write(model_names='stock.picking')
def delay_export_picking_write(session, model_name, record_id, vals):
    picking = session.env[model_name].browse(record_id)
    up_fields = ["date_done", "move_type", "carrier_name", "carrier_tracking_ref",
                 "state", "not_sync", "company_id", "partner_id"]
    if picking.partner_id.commercial_partner_id.web \
            and picking.partner_id.commercial_partner_id.active \
            and picking.picking_type_id.code == 'outgoing' \
            and not picking.not_sync \
            and picking.company_id.id == 1:
        if 'name' in vals or 'partner_id' in vals:
            export_picking.delay(session, model_name, record_id, priority=1, eta=60)
            picking_products = session.env['stock.move'].search([('picking_id', '=', picking.id)])
            for product in picking_products:
                export_pickingproduct.delay(session, 'stock.move', product.id, priority=1, eta=120)
        elif 'state' in vals and vals['state'] == 'cancel' \
                or 'not_sync' in vals and vals['not_sync'] \
                or 'company_id' in vals and vals['company_id'] != 1:
            picking_products = session.env['stock.move'].search([('picking_id', '=', picking.id)])
            for product in picking_products:
                unlink_pickingproduct.delay(session, 'stock.move', product.id, priority=1, eta=120)
            unlink_picking.delay(session, model_name, record_id, priority=5, eta=120)
        else:
            for field in up_fields:
                if field in vals:
                    update_picking.delay(session, model_name, record_id, priority=2, eta=120)
                    break
    else:
        job = session.env['queue.job'].search([('func_string', 'like', '%, ' + str(record_id) + ')%'),
                                               ('model_name', '=', model_name)], order='date_created desc', limit=1)

        if job and 'unlink' not in job.name:
            unlink_picking.delay(session, model_name, record_id, priority=5, eta=120)


@on_record_unlink(model_names='stock.picking')
def delay_export_picking_unlink(session, model_name, record_id):
    picking = session.env[model_name].browse(record_id)
    if picking.partner_id.commercial_partner_id.web \
            and picking.partner_id.commercial_partner_id.active \
            and picking.picking_type_id.code == 'outgoing' \
            and not picking.not_sync \
            and picking.company_id.id == 1:
        picking_products = session.env['stock.move'].search([('picking_id', '=', picking.id)])
        for product in picking_products:
            unlink_pickingproduct.delay(session, 'stock.move', product.id, priority=1, eta=120)
        unlink_picking.delay(session, model_name, record_id, priority=5, eta=120)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_picking(session, model_name, record_id):
    picking_exporter = _get_exporter(session, model_name, record_id,
                                     PickingExporter)
    return picking_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_picking(session, model_name, record_id):
    picking_exporter = _get_exporter(session, model_name, record_id,
                                     PickingExporter)
    return picking_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_picking(session, model_name, record_id):
    picking_exporter = _get_exporter(session, model_name, record_id,
                                     PickingExporter)
    return picking_exporter.delete(record_id)


@middleware
class PickingProductExporter(Exporter):

    _model_name = ['stock.move']

    def update(self, binding_id, mode):
        picking_line = self.model.browse(binding_id)
        vals = {
            "odoo_id": picking_line.id,
            "product_id": picking_line.product_id.id,
            "product_qty": picking_line.product_uom_qty,
            "picking_id": picking_line.picking_id.id
        }

        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class PickingProductAdapter(GenericAdapter):
    _model_name = 'stock.move'
    _middleware_model = 'pickingproduct'


@on_record_create(model_names='stock.move')
def delay_export_picking_line_create(session, model_name, record_id, vals=None):
    move_line = session.env[model_name].browse(record_id)
    if move_line.picking_id.partner_id.commercial_partner_id.web \
            and move_line.picking_id.partner_id.commercial_partner_id.active \
            and move_line.picking_id.partner_id.active \
            and move_line.picking_id.picking_type_id.code == 'outgoing' \
            and not move_line.picking_id.not_sync \
            and move_line.picking_id.company_id == 1:
        export_pickingproduct.delay(session, model_name, record_id, priority=1, eta=180)


@on_record_write(model_names='stock.move')
def delay_export_picking_line_write(session, model_name, record_id, vals):
    up_fields = ["parent_id", "product_uom_qty", "product_id"]
    move_line = session.env[model_name].browse(record_id)
    if move_line.picking_id.partner_id.commercial_partner_id.web \
            and move_line.picking_id.partner_id.commercial_partner_id.active \
            and move_line.picking_id.partner_id.active \
            and move_line.picking_id.picking_type_id.code == 'outgoing'\
            and not move_line.picking_id.not_sync \
            and move_line.picking_id.company_id == 1:
        for field in up_fields:
            if field in vals:
                update_pickingproduct.delay(session, model_name, record_id, priority=2, eta=240)


@on_record_unlink(model_names='stock.move')
def delay_export_picking_line_unlink(session, model_name, record_id):
    move_line = session.env[model_name].browse(record_id)
    if move_line.picking_id.partner_id.commercial_partner_id.web \
            and move_line.picking_id.partner_id.commercial_partner_id.active \
            and move_line.picking_id.partner_id.active \
            and move_line.picking_id.picking_type_id.code == 'outgoing' \
            and not move_line.picking_id.not_sync \
            and move_line.picking_id.company_id == 1:
        unlink_pickingproduct.delay(session, model_name, record_id, priority=5, eta=240)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_pickingproduct(session, model_name, record_id):
    picking_product_exporter = _get_exporter(session, model_name, record_id,
                                             PickingProductExporter)
    return picking_product_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_pickingproduct(session, model_name, record_id):
    picking_product_exporter = _get_exporter(session, model_name, record_id,
                                             PickingProductExporter)
    return picking_product_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_pickingproduct(session, model_name, record_id):
    picking_product_exporter = _get_exporter(session, model_name, record_id,
                                             PickingProductExporter)
    return picking_product_exporter.delete(record_id)