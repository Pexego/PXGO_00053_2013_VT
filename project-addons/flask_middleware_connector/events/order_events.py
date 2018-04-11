# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Visiotech All Rights Reserved
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
from openerp import models
from openerp.addons.connector.event import on_record_create, on_record_write, \
    on_record_unlink
from openerp.addons.connector.queue.job import job
from .utils import _get_exporter
from ..backend import middleware
from openerp.addons.connector.unit.synchronizer import Exporter
from ..unit.backend_adapter import GenericAdapter


@middleware
class OrderExporter(Exporter):

    _model_name = ['sale.order']

    def update(self, binding_id, mode):
        order = self.model.browse(binding_id)
        state = order.state
        if state in ('shipping_except', 'invoice_except'):
            state = 'done'
        vals = {"odoo_id": order.id,
                "name": order.name,
                "state": state,
                "partner_id": order.partner_id.id,
                "amount_total": order.amount_total,
                "date_order": order.date_order,
                "amount_untaxed": order.amount_untaxed,
                "client_order_ref": order.client_order_ref,
                'shipping_street': order.partner_shipping_id.street,
                'shipping_zip': order.partner_shipping_id.zip,
                'shipping_city': order.partner_shipping_id.city,
                'shipping_state': order.partner_shipping_id.state_id.name,
                'shipping_country': order.partner_shipping_id.country_id.name,
                'delivery_type': order.delivery_type,
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class OrderAdapter(GenericAdapter):
    _model_name = 'sale.order'
    _middleware_model = 'order'


@on_record_create(model_names='sale.order')
def delay_export_order_create(session, model_name, record_id, vals):
    order = session.env[model_name].browse(record_id)
    if order.partner_id.web or order.partner_id.commercial_partner_id.web:
        export_order.delay(session, model_name, record_id, priority=2, eta=80)


@on_record_write(model_names='sale.order')
def delay_export_order_write(session, model_name, record_id, vals):
    order = session.env[model_name].browse(record_id)
    #He cogido order_line porque no entra amount_total ni amount_untaxed en el write
    up_fields = ["name", "state", "partner_id", "date_order", "client_order_ref",
                 "order_line", "partner_shipping_id", "delivery_type"]
    if order.partner_id.web or order.partner_id.commercial_partner_id.web:
        job = session.env['queue.job'].search([('func_string', 'like', '%, ' + str(order.id) + ')%'),
                                               ('model_name', '=', model_name)], order='date_created desc', limit=1)
        if 'state' in vals.keys() and vals['state'] == 'cancel':
            unlink_order.delay(session, model_name, record_id, priority=7, eta=180)
        elif 'state' in vals.keys() and vals['state'] in ('draft', 'reserve') and job.name and 'unlink' in job.name:
            export_order.delay(session, model_name, record_id, priority=2, eta=80)
            for line in order.order_line:
                export_orderproduct.delay(session, 'sale.order.line', line.id, priority=2, eta=120)
        elif order.state in ('draft', 'reserve', 'progress', 'done', 'shipping_except', 'invoice_except'):
            for field in up_fields:
                if field in vals:
                    update_order.delay(session, model_name, record_id, priority=5, eta=120)
                    break


@on_record_unlink(model_names='sale.order')
def delay_export_order_unlink(session, model_name, record_id):
    order = session.env[model_name].browse(record_id)
    if order.partner_id.web or order.partner_id.commercial_partner_id.web:
        unlink_order.delay(session, model_name, record_id, priority=7, eta=180)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_order(session, model_name, record_id):
    order_exporter = _get_exporter(session, model_name, record_id,
                                   OrderExporter)
    return order_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_order(session, model_name, record_id):
    order_exporter = _get_exporter(session, model_name, record_id,
                                   OrderExporter)
    return order_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_order(session, model_name, record_id):
    order_exporter = _get_exporter(session, model_name, record_id,
                                   OrderExporter)
    return order_exporter.delete(record_id)

@middleware
class OrderProductExporter(Exporter):

    _model_name = ['sale.order.line']

    def update(self, binding_id, mode):
        orderproduct = self.model.browse(binding_id)
        vals = {"odoo_id": orderproduct.id,
                "product_id": orderproduct.product_id.id,
                "product_qty": orderproduct.product_uom_qty,
                "price_subtotal": orderproduct.price_subtotal,
                "order_id": orderproduct.order_id.id,
                "no_rappel": orderproduct.no_rappel,
                "deposit": orderproduct.deposit,
                "pack_parent_line_id": orderproduct.pack_parent_line_id.id,
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)

@middleware
class OrderProductAdapter(GenericAdapter):
    _model_name = 'sale.order.line'
    _middleware_model = 'orderproduct'


@on_record_create(model_names='sale.order.line')
def delay_export_orderproduct_create(session, model_name, record_id, vals):
    orderproduct = session.env[model_name].browse(record_id)
    if orderproduct.order_id.partner_id.web or orderproduct.order_id.partner_id.commercial_partner_id.web:
        export_orderproduct.delay(session, model_name, record_id, priority=2, eta=120)


@on_record_write(model_names='sale.order.line')
def delay_export_orderproduct_write(session, model_name, record_id, vals):
    orderproduct = session.env[model_name].browse(record_id)
    up_fields = ["product_id", "product_uom_qty", "price_unit", "discount", "order_id",
                 "no_rappel", "deposit", "pack_parent_line_id"]
    if orderproduct.order_id.partner_id.web or orderproduct.order_id.partner_id.commercial_partner_id.web:
        for field in up_fields:
            if field in vals:
                update_orderproduct.delay(session, model_name, record_id, priority=5, eta=120)
                break


@on_record_unlink(model_names='sale.order.line')
def delay_export_orderproduct_unlink(session, model_name, record_id):
    orderproduct = session.env[model_name].browse(record_id)
    if orderproduct.order_id.partner_id.web or orderproduct.order_id.partner_id.commercial_partner_id.web:
        unlink_orderproduct.delay(session, model_name, record_id, priority=7, eta=180)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_orderproduct(session, model_name, record_id):
    orderproduct_exporter = _get_exporter(session, model_name, record_id,
                                          OrderProductExporter)
    return orderproduct_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_orderproduct(session, model_name, record_id):
    orderproduct_exporter = _get_exporter(session, model_name, record_id,
                                          OrderProductExporter)
    return orderproduct_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_orderproduct(session, model_name, record_id):
    orderproduct_exporter = _get_exporter(session, model_name, record_id,
                                          OrderProductExporter)
    return orderproduct_exporter.delete(record_id)

