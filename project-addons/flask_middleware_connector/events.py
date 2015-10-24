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
from .connector import get_environment
from .backend import middleware
from openerp.addons.connector.unit.synchronizer import Exporter
from .unit.backend_adapter import GenericAdapter
from openerp.addons.connector.event import Event

on_stock_move_change = Event()


@middleware
class ProductExporter(Exporter):

    _model_name = ['product.product']

    def update(self, binding_id, mode):
        product = self.model.browse(binding_id)
        vals = {"name": product.name,
                "code": product.default_code,
                "odoo_id": product.id,
                "uom_name": product.uom_id.name}
        vals["price_unit"] = eval("product." + self.backend_record.
                                  price_unit_field_id.name,
                                  {'product': product})
        if product.show_stock_outside:
            stock_qty = eval("product." + self.backend_record.
                             product_stock_field_id.name,
                             {'product': product})
            if stock_qty <= 0.0:
                vals["stock"] = 0.0
            else:
                vals["stock"] = stock_qty
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class PartnerExporter(Exporter):

    _model_name = ['res.partner']

    def update(self, binding_id, mode):
        partner = self.model.browse(binding_id)
        vals = {"fiscal_name": partner.name,
                "commercial_name": partner.comercial or "",
                "odoo_id": partner.id,
                "vat": partner.vat or "",
                "street": partner.street or "",
                "city": partner.city or "",
                "zipcode": partner.zip,
                "country": partner.country_id and partner.country_id.name or
                "",
                "state": partner.state_id and partner.state_id.name or "",
                "email": partner.email or ""}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class ProductAdapter(GenericAdapter):
    _model_name = 'product.product'
    _middleware_model = 'product'


@middleware
class PartnerAdapter(GenericAdapter):
    _model_name = 'res.partner'
    _middleware_model = 'customer'


@on_record_create(model_names='product.product')
def delay_export_product1(session, model_name, record_id, vals):
    product = session.env[model_name].browse(record_id)
    up_fields = ["name", "default_code", "list_price", "list_price2",
                 "list_price3"]
    if vals.get("web", False) and vals.get("web", False) == "published":
        export_product.delay(session, model_name, record_id)
    elif product.web == "published":
        for field in up_fields:
            if field in vals:
                update_product.delay(session, model_name, record_id)
                break

@on_record_write(model_names='product.product')
def delay_export_product2(session, model_name, record_id, vals):
    product = session.env[model_name].browse(record_id)
    up_fields = ["name", "default_code", "list_price", "list_price2",
                 "list_price3"]
    if vals.get("web", False) and vals.get("web", False) == "published":
        export_product.delay(session, model_name, record_id)
    elif vals.get("web", False) and vals.get("web", False) != "published":
        unlink_product(session, model_name, record_id)
    elif product.web == "published":
        for field in up_fields:
            if field in vals:
                update_product.delay(session, model_name, record_id)
                break


@on_record_create(model_names='res.partner')
def delay_export_partner1(session, model_name, record_id, vals):
    partner = session.env[model_name].browse(record_id)
    up_fields = ["name", "comercial", "vat", "city", "street", "zip",
                 "country_id", "state_id", "email"]
    if vals.get("web", False) and (vals.get('active', False) or
                                   partner.active):
        export_partner.delay(session, model_name, record_id)
    elif vals.get("active", False) and partner.web:
        export_partner.delay(session, model_name, record_id)
    elif partner.web:
        for field in up_fields:
            if field in vals:
                update_partner.delay(session, model_name, record_id)
                break

@on_record_write(model_names='res.partner')
def delay_export_partner2(session, model_name, record_id, vals):
    partner = session.env[model_name].browse(record_id)
    up_fields = ["name", "comercial", "vat", "city", "street", "zip",
                 "country_id", "state_id", "email"]
    if vals.get("web", False) and (vals.get('active', False) or
                                   partner.active):
        export_partner.delay(session, model_name, record_id)
    elif "web" in vals and not vals["web"]:
        unlink_partner(session, model_name, record_id)
    elif vals.get("active", False) and partner.web:
        export_partner.delay(session, model_name, record_id)
    elif "active" in vals and not vals["active"] and partner.web:
        unlink_partner(session, model_name, record_id)
    elif partner.web:
        for field in up_fields:
            if field in vals:
                update_partner.delay(session, model_name, record_id)
                break

@on_record_unlink(model_names='product.product')
def delay_unlink_product(session, model_name, record_id):
    product = session.env[model_name].browse(record_id)
    if product.web == "published":
        unlink_product.delay(session, model_name, record_id)


@on_record_unlink(model_names='res.partner')
def delay_unlink_partner(session, model_name, record_id):
    partner = session.env[model_name].browse(record_id)
    if partner.web:
        unlink_partner.delay(session, model_name, record_id)


@on_stock_move_change
def update_stock_quantity(session, model_name, record_id):
    move = session.env[model_name].browse(record_id)
    if move.product_id.web == "published" and \
            move.product_id.show_stock_outside:
        update_product.delay(session, "product.product", move.product_id.id)


@job
def export_product(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    product_exporter = env.get_connector_unit(ProductExporter)
    return product_exporter.update(record_id, "insert")


@job
def export_partner(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    partner_exporter = env.get_connector_unit(PartnerExporter)
    return partner_exporter.update(record_id, "insert")


@job
def update_product(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    product_exporter = env.get_connector_unit(ProductExporter)
    return product_exporter.update(record_id, "update")


@job
def update_partner(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    partner_exporter = env.get_connector_unit(PartnerExporter)
    return partner_exporter.update(record_id, "update")


@job
def unlink_product(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    product_exporter = env.get_connector_unit(ProductExporter)
    return product_exporter.delete(record_id)


@job
def unlink_partner(session, model_name, record_id):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    partner_exporter = env.get_connector_unit(PartnerExporter)
    return partner_exporter.delete(record_id)
