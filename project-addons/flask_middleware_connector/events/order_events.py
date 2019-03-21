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
# class OrderExporter(Exporter):
#
#     _model_name = ['sale.order']
#
#     def update(self, binding_id, mode):
#         order = self.model.browse(binding_id)
#         state = order.state
#         if state in ('shipping_except', 'invoice_except'):
#             state = 'done'
#         vals = {"odoo_id": order.id,
#                 "name": order.name,
#                 "state": state,
#                 "partner_id": order.partner_id.id,
#                 "amount_total": order.amount_total,
#                 "date_order": order.date_order,
#                 "amount_untaxed": order.amount_untaxed,
#                 "client_order_ref": order.client_order_ref,
#                 'shipping_street': order.partner_shipping_id.street,
#                 'shipping_zip': order.partner_shipping_id.zip,
#                 'shipping_city': order.partner_shipping_id.city,
#                 'shipping_state': order.partner_shipping_id.state_id.name,
#                 'shipping_country': order.partner_shipping_id.country_id.name,
#                 'delivery_type': order.delivery_type,
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
# class OrderAdapter(GenericAdapter):
#     _model_name = 'sale.order'
#     _middleware_model = 'order'


class SaleOrderListener(Component):
    _name = 'sale.order.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order']

    def on_record_create(self, record, fields=None):
        if record.partner_id.web or record.partner_id.commercial_partner_id.web:
            record.with_delay(priority=2, eta=80).export_order()

    def on_record_write(self, record, fields=None):
        # He cogido order_line porque no entra amount_total ni amount_untaxed en el write
        up_fields = ["name", "state", "partner_id", "date_order", "client_order_ref",
                     "order_line", "partner_shipping_id", "delivery_type"]
        model_name = 'sale.order'
        if record.partner_id.web or record.partner_id.commercial_partner_id.web:
            job = self.env['queue.job'].sudo().search([('func_string', 'like', '%, ' + str(record.id) + ')%'),
                                                      ('model_name', '=', model_name)],
                                                      order='date_created desc, id desc', limit=1)
            if 'state' in fields and record.state == 'cancel':
                record.with_delay(priority=7, eta=80).unlink_order()
            elif 'state' in fields and record.state in ('draft', 'reserve') and job.name and 'unlink' in job.name:
                record.with_delay(priority=2, eta=80).export_order()
                for line in record.order_line:
                    line.with_delay(priority=2, eta=120).export_orderproduct()
            elif record.state in ('draft', 'reserve', 'progress', 'done', 'shipping_except', 'invoice_except'):
                for field in up_fields:
                    if field in fields:
                        record.with_delay(priority=5, eta=80).update_order(fields=fields)
                        break

    def on_record_unlink(self, record):
        if record.partner_id.web or record.partner_id.commercial_partner_id.web:
            record.with_delay(priority=7, eta=180).unlink_order()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_order(self):
        # order_exporter = _get_exporter(session, model_name, record_id,
        #                                OrderExporter)
        # return order_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_order(self, fields):
        # order_exporter = _get_exporter(session, model_name, record_id,
        #                                OrderExporter)
        # return order_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_order(self):
        # order_exporter = _get_exporter(session, model_name, record_id,
        #                                OrderExporter)
        # return order_exporter.delete(record_id)
        return True

# TODO: Migrar parte del adapter
# @middleware
# class OrderProductExporter(Exporter):
#
#     _model_name = ['sale.order.line']
#
#     def update(self, binding_id, mode):
#         orderproduct = self.model.browse(binding_id)
#         vals = {"odoo_id": orderproduct.id,
#                 "product_id": orderproduct.product_id.id,
#                 "product_qty": orderproduct.product_uom_qty,
#                 "price_subtotal": orderproduct.price_subtotal,
#                 "order_id": orderproduct.order_id.id,
#                 "no_rappel": orderproduct.no_rappel,
#                 "deposit": orderproduct.deposit,
#                 #TODO: Migrar "pack_parent_line_id": orderproduct.pack_parent_line_id.id,
#                 "discount": orderproduct.discount,
#                 "price_unit": orderproduct.price_unit,
#         }
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(binding_id, vals)
#
#     def delete(self, binding_id):
#         return self.backend_adapter.remove(binding_id)
#
# @middleware
# class OrderProductAdapter(GenericAdapter):
#     _model_name = 'sale.order.line'
#     _middleware_model = 'orderproduct'


class SaleOrderLineListener(Component):
    _name = 'sale.order.line.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['sale.order.line']

    def on_record_create(self, record, fields=None):
        if record.order_id.partner_id.web or record.order_id.partner_id.commercial_partner_id.web:
            record.with_delay(priority=2, eta=120).export_orderproduct()

    def on_record_write(self, record, fields=None):
        up_fields = ["product_id", "product_uom_qty", "price_unit", "discount", "order_id",
                     "no_rappel", "deposit", "price_unit",
                     "no_rappel", "deposit", "pack_parent_line_id", "price_unit"]
        if record.order_id.partner_id.web or record.order_id.partner_id.commercial_partner_id.web:
            for field in up_fields:
                if field in fields:
                    record.with_delay(priority=5, eta=120).update_orderproduct(fields=fields)
                    break

    def on_record_unlink(self, record):
        if record.order_id.partner_id.web or record.order_id.partner_id.commercial_partner_id.web:
            record.with_delay(priority=7, eta=180).unlink_orderproduct()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_orderproduct(self):
        # orderproduct_exporter = _get_exporter(session, model_name, record_id,
        #                                       OrderProductExporter)
        # return orderproduct_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_orderproduct(self, fields):
        # orderproduct_exporter = _get_exporter(session, model_name, record_id,
        #                                       OrderProductExporter)
        # return orderproduct_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_orderproduct(self):
        # orderproduct_exporter = _get_exporter(session, model_name, record_id,
        #                                       OrderProductExporter)
        # return orderproduct_exporter.delete(record_id)
        return True

