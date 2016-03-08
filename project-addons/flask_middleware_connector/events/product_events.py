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
from .rma_events import export_rmaproduct
from openerp.addons.connector.event import Event

on_stock_move_change = Event()


@middleware
class ProductExporter(Exporter):

    _model_name = ['product.product']

    def update(self, binding_id, mode):
        product = self.model.browse(binding_id)
        vals = {'name': product.name,
                'code': product.default_code,
                'odoo_id': product.id,
                'categ_id': product.categ_id.id,
                'pvi_1': product.pvi1_price,
                'pvi_2': product.pvi2_price,
                'pvi_3': product.pvi3_price,
                'uom_name': product.uom_id.name,
                'last_sixty_days_sales': product.last_sixty_days_sales,
                'brand_id': product.product_brand_id.id}
        vals['pvd_1'] = product.lst_price - (product.pvd1_relation *
                                             product.lst_price)
        vals['pvd_2'] = product.list_price2 - (product.pvd2_relation *
                                               product.list_price2)
        vals['pvd_3'] = product.list_price3 - (product.pvd3_relation *
                                               product.list_price3)
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
class ProductAdapter(GenericAdapter):
    _model_name = 'product.product'
    _middleware_model = 'product'


@on_record_create(model_names='product.product')
def delay_export_product_create(session, model_name, record_id, vals):
    product = session.env[model_name].browse(record_id)
    up_fields = ["name", "default_code", "pvi1_price", "pvi2_price",
                 "pvi3_price", "lst_price", "list_price2", "list_price3",
                 "pvd1_relation", "pvd2_relation", "pvd3_relation", "categ_id",
                 "product_brand_id", "last_sixty_days_sales"]
    if vals.get("web", False) and vals.get("web", False) == "published":
        export_product.delay(session, model_name, record_id, priority=2, eta=60)
        claim_lines = session.env['claim.line'].search(
            [('product_id', '=', product.id),
             ('claim_id.partner_id.web', '=', True)])
        for line in claim_lines:
            export_rmaproduct.delay(session, 'claim.line', line.id,
                                    priority=10, eta=120)
    elif product.web == "published":
        for field in up_fields:
            if field in vals:
                update_product.delay(session, model_name, record_id)
                break


@on_record_write(model_names='product.product')
def delay_export_product_write(session, model_name, record_id, vals):
    product = session.env[model_name].browse(record_id)
    up_fields = ["name", "default_code", "pvi1_price", "pvi2_price",
                 "pvi3_price", "lst_price", "list_price2", "list_price3",
                 "pvd1_relation", "pvd2_relation", "pvd3_relation", "categ_id",
                 "product_brand_id", "last_sixty_days_sales"]
    if vals.get("web", False) and vals.get("web", False) == "published":
        export_product.delay(session, model_name, record_id, priority=2, eta=60)
        claim_lines = session.env['claim.line'].search(
            [('product_id', '=', product.id),
             ('claim_id.partner_id.web', '=', True)])
        for line in claim_lines:
            export_rmaproduct.delay(session, 'claim.line', line.id,
                                    priority=10, eta=120)
    elif vals.get("web", False) and vals.get("web", False) != "published":
        unlink_product.delay(session, model_name, record_id, priority=1)
    elif product.web == "published":
        for field in up_fields:
            if field in vals:
                update_product.delay(session, model_name, record_id)
                break


@on_record_unlink(model_names='product.product')
def delay_unlink_product(session, model_name, record_id):
    product = session.env[model_name].browse(record_id)
    if product.web == "published":
        unlink_product.delay(session, model_name, record_id)


@on_stock_move_change
def update_stock_quantity(session, model_name, record_id):
    move = session.env[model_name].browse(record_id)
    if move.product_id.web == "published" and \
            move.product_id.show_stock_outside:
        update_product.delay(session, "product.product", move.product_id.id)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_product(session, model_name, record_id):
    product_exporter = _get_exporter(session, model_name, record_id,
                                     ProductExporter)
    return product_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_product(session, model_name, record_id):
    product_exporter = _get_exporter(session, model_name, record_id,
                                     ProductExporter)
    return product_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_product(session, model_name, record_id):
    product_exporter = _get_exporter(session, model_name, record_id,
                                     ProductExporter)
    return product_exporter.delete(record_id)


@middleware
class ProductCategoryExporter(Exporter):

    _model_name = ['product.category']

    def update(self, binding_id, mode):
        category = self.model.browse(binding_id)
        vals = {"name": category.name,
                "parent_id": category.parent_id.id,
                "odoo_id": category.id}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class ProductCategoryAdapter(GenericAdapter):
    _model_name = 'product.category'
    _middleware_model = 'productcategory'


@on_record_create(model_names='product.category')
def delay_export_product_category_create(session, model_name, record_id, vals):
    export_product_category.delay(session, model_name, record_id, priority=1)


@on_record_write(model_names='product.category')
def delay_export_product_category_write(session, model_name, record_id, vals):
    category = session.env[model_name].browse(record_id)
    up_fields = ["name", "parent_id"]
    for field in up_fields:
        if field in vals:
            update_product_category.delay(session, model_name, record_id)
            break


@on_record_unlink(model_names='product.category')
def delay_unlink_product_category(session, model_name, record_id):
    unlink_product_category.delay(session, model_name, record_id)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_product_category(session, model_name, record_id):
    category_exporter = _get_exporter(session, model_name, record_id,
                                      ProductCategoryExporter)
    return category_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_product_category(session, model_name, record_id):
    category_exporter = _get_exporter(session, model_name, record_id,
                                      ProductCategoryExporter)
    return category_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_product_category(session, model_name, record_id):
    category_exporter = _get_exporter(session, model_name, record_id,
                                      ProductCategoryExporter)
    return category_exporter.delete(record_id)


@middleware
class ProductbrandExporter(Exporter):

    _model_name = ['product.brand']

    def update(self, binding_id, mode):
        brand = self.model.browse(binding_id)
        vals = {"name": brand.name,
                "odoo_id": brand.id}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class ProductbrandAdapter(GenericAdapter):
    _model_name = 'product.brand'
    _middleware_model = 'productbrand'


@on_record_create(model_names='product.brand')
def delay_export_product_brand_create(session, model_name, record_id, vals):
    export_product_brand.delay(session, model_name, record_id, priority=0)


@on_record_write(model_names='product.brand')
def delay_export_product_brand_write(session, model_name, record_id, vals):
    brand = session.env[model_name].browse(record_id)
    up_fields = ["name"]
    for field in up_fields:
        if field in vals:
            update_product_brand.delay(session, model_name, record_id)
            break


@on_record_unlink(model_names='product.brand')
def delay_unlink_product_brand(session, model_name, record_id):
    unlink_product_brand.delay(session, model_name, record_id)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_product_brand(session, model_name, record_id):
    brand_exporter = _get_exporter(session, model_name, record_id,
                                      ProductbrandExporter)
    return brand_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_product_brand(session, model_name, record_id):
    brand_exporter = _get_exporter(session, model_name, record_id,
                                      ProductbrandExporter)
    return brand_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_product_brand(session, model_name, record_id):
    brand_exporter = _get_exporter(session, model_name, record_id,
                                      ProductbrandExporter)
    return brand_exporter.delete(record_id)


@middleware
class ProductbrandRelExporter(Exporter):

    _model_name = ['brand.country.rel']

    def update(self, binding_id, mode):
        brand_rel = self.model.browse(binding_id)
        vals = {
                "country_id": brand_rel.country_id.id,
                "brand_id": brand_rel.brand_id.id,
                "odoo_id": brand_rel.id}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@middleware
class ProductbranreldAdapter(GenericAdapter):
    _model_name = 'brand.country.rel'
    _middleware_model = 'productbrandcountryrel'


@on_record_create(model_names='brand.country.rel')
def delay_export_product_brand_rel_create(session, model_name, record_id, vals):
    export_product_brand_rel.delay(session, model_name, record_id, priority=50)


@on_record_write(model_names='brand.country.rel')
def delay_export_product_brand_rel_write(session, model_name, record_id, vals):
    brand = session.env[model_name].browse(record_id)
    up_fields = ["brand_id", "country_id"]
    for field in up_fields:
        if field in vals:
            update_product_brand_rel.delay(session, model_name, record_id, delay=50)
            break


@on_record_unlink(model_names='brand.country.rel')
def delay_unlink_product_brand_rel(session, model_name, record_id):
    unlink_product_brand_rel.delay(session, model_name, record_id, priority=1)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_product_brand_rel(session, model_name, record_id):
    brand_exporter = _get_exporter(session, model_name, record_id,
                                      ProductbrandRelExporter)
    return brand_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_product_brand_rel(session, model_name, record_id):
    brand_exporter = _get_exporter(session, model_name, record_id,
                                      ProductbrandRelExporter)
    return brand_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_product_brand_rel(session, model_name, record_id):
    brand_exporter = _get_exporter(session, model_name, record_id,
                                      ProductbrandRelExporter)
    return brand_exporter.delete(record_id)
