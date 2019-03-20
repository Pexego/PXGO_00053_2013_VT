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

# TODO: Migrar la parte del adapter
# @middleware
# class ProductExporter(Exporter):
#
#     _model_name = ['product.product', 'product.template']
#
#     def update(self, binding_id, mode):
#         if self.model == self.env["product.template"]:
#             products = self.env["product.product"].\
#                 search([('product_tmpl_id', '=', binding_id)])
#         else:
#             products = [self.model.browse(binding_id)]
#         for product in products:
#             vals = {'name': product.name,
#                     'code': product.default_code,
#                     'odoo_id': product.id,
#                     'categ_id': product.categ_id.id,
#                     'pvi_1': product.pvi1_price,
#                     'pvi_2': product.pvi2_price,
#                     'pvi_3': product.pvi3_price,
#                     'pvi_4': product.pvi4_price,
#                     'uom_name': product.uom_id.name,
#                     'last_sixty_days_sales': product.last_sixty_days_sales,
#                     'brand_id': product.product_brand_id.id,
#                     'pvd_1': product.pvd1_price,
#                     'pvd_2': product.pvd2_price,
#                     'pvd_3': product.pvd3_price,
#                     'pvd_4': product.pvd4_price,
#                     'pvm': product.product_tmpl_id.pvm_price,
#                     'joking_index': product.joking_index,
#                     'sale_ok': product.sale_ok,
#                     'ean13': product.ean13,
#                     'manufacturer_ref': product.manufacturer_pref,
#                     'description_sale': product.description_sale,
#                     'type': product.type,
#                     'is_pack': product.is_pack,
#                     'discontinued': product.discontinued,
#                     'state': product.state}
#             if product.show_stock_outside:
#                 vals['external_stock'] = product.qty_available_external
#                 stock_qty = eval("product." + self.backend_record.
#                                  product_stock_field_id.name,
#                                  {'product': product})
#                 vals["stock"] = stock_qty
#             if mode == "insert":
#                 self.backend_adapter.insert(vals)
#             else:
#                 self.backend_adapter.update(product.id, vals)
#         return True
#
#     def delete(self, binding_id):
#         if self.model._name == "product.template":
#             products = self.env["product.product"].\
#                 search([('product_tmpl_id', '=', binding_id)])
#         else:
#             products = [self.model.browse(binding_id)]
#         for product in products:
#             self.backend_adapter.remove(product.id)
#         return True
#
# @middleware
# class ProductTemplateAdapter(GenericAdapter):
#     _model_name = 'product.template'
#     _middleware_model = 'product'
#
#
# @middleware
# class ProductAdapter(GenericAdapter):
#     _model_name = 'product.product'
#     _middleware_model = 'product'


class ProductTemplateListener(Component):
    _name = 'product.template.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['product.template']

    def on_record_write(self, record, fields=None):
        up_fields = ["name", "list_price", "categ_id", "product_brand_id", "show_stock_outside", "sale_ok"]
        if record.image or len(fields) != 1:
            for field in up_fields:
                if field in fields:
                    product = self.env["product.product"].search([('product_tmpl_id', '=', record.id)])
                    #TODO: revisar, no funciona: update_product() missing 1 required positional argument: 'fields'
                    product.with_delay(priority=3, eta=60).update_product(fields=fields)
                    break


class ProductListener(Component):
    _name = 'product.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['product.product']

    def on_record_create(self, record, fields=None):
        up_fields = ["name", "default_code", "pvi1_price", "pvi2_price", "pvi3_price", "pvi4_price",
                     "list_price", "list_price2", "list_price3", "list_price4",
                     "pvd1_relation", "pvd2_relation", "pvd3_relation", "pvd4_relation",
                     "categ_id", "product_brand_id", "last_sixty_days_sales",
                     "joking_index", "sale_ok", "ean13", "description_sale",
                     "manufacturer_pref", "standard_price", "type", #TODO:Migrar "pack_line_ids",
                     "discontinued", "state"]
        record.with_delay().export_product()
        claim_lines = self.env['claim.line'].search(
                                            [('product_id', '=', record.id),
                                             ('claim_id.partner_id.web', '=', True)])
        for line in claim_lines:
            if not line.equivalent_product_id:
                line.with_delay(priority=10, eta=120).export_rmaproduct()
        claim_lines = self.env['claim.line'].search(
                                            [('equivalent_product_id', '=', record.id),
                                             ('claim_id.partner_id.web', '=', True)])
        for line in claim_lines:
            line.with_delay(priority=10, eta=120).export_rmaproduct()

    def on_record_write(self, record, fields=None):
        up_fields = ["default_code", "pvi1_price", "pvi2_price", "pvi3_price", "pvi4_price",
                     "list_price2", "list_price3", "list_price4",
                     "pvd1_relation", "pvd2_relation", "pvd3_relation", "pvd4_relation",
                     "last_sixty_days_sales", "joking_index", "sale_ok",
                     "ean13", "description_sale", "manufacturer_pref", "standard_price",
                     "type", "discontinued", "state",
                     "type",  # "pack_line_ids",
                     "discontinued", "state"]
        for field in up_fields:
            if field in fields:
                record.with_delay(priority=2, eta=30).update_product(fields=fields)
                break
        #TODO: Migrar
        # ~ is_pack = session.env['product.pack.line'].search([('product_id', '=', record_id)])
        # ~ for pack in is_pack:
            # ~ min_stock = False
            # ~ for product in pack.parent_product_id.pack_line_ids:
                # ~ product_stock_qty = product.product_id.virtual_available_wo_incoming
                # ~ if not min_stock or min_stock > product_stock_qty:
                    # ~ min_stock = product_stock_qty
            # ~ if min_stock:
                # ~ update_product.delay(session, model_name, pack.parent_product_id.id, priority=2, eta=30)

        if 'tag_ids' in fields:
            record.with_delay(priority=5, eta=60).unlink_product_tag_rel()
            tag_ids = fields.tag_ids[0][-1]
            if type(tag_ids) is int:
                tag_ids = [tag_ids]
            for tag_id in tag_ids:
                # TODO: Revisar, ¿pasar tag_id?
                record.with_delay(priority=2, eta=120).export_product_tag_rel()

    def on_record_unlink(self, record):
        record.with_delay().unlink_product()

# TODO:Migrar
# @on_stock_move_change
# def update_stock_quantity(session, model_name, record_id):
#     move = session.env[model_name].browse(record_id)
#     if move.product_id.show_stock_outside:
#         update_product.delay(session, "product.product", move.product_id.id, priority=2, eta=30)
#     #TODO: Migrar
#     # ~ is_pack = session.env['product.pack.line'].search([('product_id', '=', move.product_id.id)])
#     # ~ for pack in is_pack:
#         # ~ update_product.delay(session, "product.product", pack.parent_product_id.id, priority=2, eta=30)


class ProductTemplate(models.Model):
    _inherit = 'product.product'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_product(self):
        # product_exporter = _get_exporter(session, model_name, record_id,
        #                                  ProductExporter)
        # return product_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_product(self, fields):
        # product_exporter = _get_exporter(session, model_name, record_id,
        #                                  ProductExporter)
        # return product_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_product(self):
        # product_exporter = _get_exporter(session, model_name, record_id,
        #                                  ProductExporter)
        # return product_exporter.delete(record_id)
        return True

#
# @middleware
# class ProductCategoryExporter(Exporter):
#
#     _model_name = ['product.category']
#
#     def update(self, binding_id, mode):
#         category = self.model.browse(binding_id)
#         vals = {"name": category.name,
#                 "parent_id": category.parent_id.id,
#                 "odoo_id": category.id}
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
# class ProductCategoryAdapter(GenericAdapter):
#     _model_name = 'product.category'
#     _middleware_model = 'productcategory'


class ProductCategoryListener(Component):
    _name = 'product.category.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['product.category']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=1).export_product_category()

    def on_record_write(self, record, fields=None):
        up_fields = ["name", "parent_id"]
        for field in up_fields:
            if field in fields:
                record.with_delay().update_product_category()
                break

    def on_record_unlink(self, record):
        record.with_delay().unlink_product_category()


class ProductCategory(models.Model):
    _inherit = 'product.category'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_product_category(self):
        # category_exporter = _get_exporter(session, model_name, record_id,
        #                                   ProductCategoryExporter)
        # return category_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_product_category(self, fields):
        # category_exporter = _get_exporter(session, model_name, record_id,
        #                                   ProductCategoryExporter)
        # return category_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_product_category(self):
        # category_exporter = _get_exporter(session, model_name, record_id,
        #                                   ProductCategoryExporter)
        # return category_exporter.delete(record_id)
        return True

# TODO: Migrar parte del adapter
# @middleware
# class ProductbrandExporter(Exporter):
#
#     _model_name = ['product.brand']
#
#     def update(self, binding_id, mode):
#         brand = self.model.browse(binding_id)
#         vals = {"name": brand.name,
#                 "odoo_id": brand.id}
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
# class ProductbrandAdapter(GenericAdapter):
#     _model_name = 'product.brand'
#     _middleware_model = 'productbrand'


class ProductBrandListener(Component):
    _name = 'product.brand.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['product.brand']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=0).export_product_brand()

    def on_record_write(self, record, fields=None):
        up_fields = ["name"]
        for field in up_fields:
            if field in fields:
                record.with_delay().update_product_brand()
                break

    def on_record_unlink(self, record):
        record.with_delay().unlink_product_brand()


class ProductBrand(models.Model):
    _inherit = 'product.brand'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_product_brand(self):
        # brand_exporter = _get_exporter(session, model_name, record_id,
        #                                   ProductbrandExporter)
        # return brand_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_product_brand(self, fields):
        # brand_exporter = _get_exporter(session, model_name, record_id,
        #                                   ProductbrandExporter)
        # return brand_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_product_brand(self):
        # brand_exporter = _get_exporter(session, model_name, record_id,
        #                                   ProductbrandExporter)
        # return brand_exporter.delete(record_id)
        return True

# TODO: Migrar parte del adapter
# @middleware
# class ProductbrandRelExporter(Exporter):
#
#     _model_name = ['brand.country.rel']
#
#     def update(self, binding_id, mode):
#         brand_rel = self.model.browse(binding_id)
#         vals = {
#                 "country_id": brand_rel.country_id.id,
#                 "brand_id": brand_rel.brand_id.id,
#                 "odoo_id": brand_rel.id}
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
# class ProductbranreldAdapter(GenericAdapter):
#     _model_name = 'brand.country.rel'
#     _middleware_model = 'productbrandcountryrel'


class BrandCountryListener(Component):
    _name = 'brand.country.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['brand.country.rel']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=50).export_product_brand_rel()

    def on_record_write(self, record, fields=None):
        up_fields = ["brand_id", "country_id"]
        for field in up_fields:
            if field in fields:
                record.with_delay(delay=50).update_product_brand_rel()
                break

    def on_record_unlink(self, record):
        record.with_delay(priority=1).unlink_product_brand_rel()


class BrandCountryRel(models.Model):
    _inherit = 'brand.country.rel'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_product_brand_rel(self):
        # brand_exporter = _get_exporter(session, model_name, record_id,
        #                                   ProductbrandRelExporter)
        # return brand_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_product_brand_rel(self, fields):
        # brand_exporter = _get_exporter(session, model_name, record_id,
        #                                   ProductbrandRelExporter)
        # return brand_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_product_brand_rel(self):
        # brand_exporter = _get_exporter(session, model_name, record_id,
        #                                   ProductbrandRelExporter)
        # return brand_exporter.delete(record_id)
        return True

# TODO: Migrar parte del adapter
# @middleware
# class ProductTagExporter(Exporter):
#
#     _model_name = ['product.tag']
#
#     def update(self, binding_id, mode):
#         tag = self.model.browse(binding_id)
#         vals = {"odoo_id": tag.id,
#                 "name": tag.name,
#                 }
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
# class ProductTagAdapter(GenericAdapter):
#     _model_name = 'product.tag'
#     _middleware_model = 'producttag'


class ProductTagsListener(Component):
    _name = 'product.tag.event.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['product.tag']

    def on_record_create(self, record, fields=None):
        record.with_delay(priority=1, eta=60).export_product_tag()

    def on_record_write(self, record, fields=None):
        record.with_delay(priority=2, eta=120).update_product_tag()

    def on_record_unlink(self, record):
        record.with_delay(priority=3, eta=120).unlink_product_tag()


class ProductTag(models.Model):
    _inherit = 'product.tag'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_product_tag(self):
        # product_tag_exporter = _get_exporter(session, model_name, record_id,
        #                                      ProductTagExporter)
        # return product_tag_exporter.update(record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def update_product_tag(self, fields):
        # product_tag_exporter = _get_exporter(session, model_name, record_id,
        #                                      ProductTagExporter)
        # return product_tag_exporter.update(record_id, "update")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_product_tag(self):
        # product_tag_exporter = _get_exporter(session, model_name, record_id,
        #                                      ProductTagExporter)
        # return product_tag_exporter.delete(record_id)
        return True

# TODO: Migrar parte del adapter
# @middleware
# class ProductTagRelExporter(Exporter):
#
#     _model_name = ['product.tag.rel']
#
#     def update(self, product_record_id, tag_record_id, mode):
#         vals = {"odoo_id": product_record_id,
#                 "producttag_id": tag_record_id,
#                 }
#         if mode == "insert":
#             return self.backend_adapter.insert(vals)
#         else:
#             return self.backend_adapter.update(product_record_id, tag_record_id, vals)
#
#     def delete(self, product_record_id):
#         return self.backend_adapter.remove(product_record_id)
#
#
# @middleware
# class ProductTagRelAdapter(GenericAdapter):
#     _model_name = 'product.tag.rel'
#     _middleware_model = 'producttagproductrel'

# TODO: Revisar, ¿Modelo correcto, faltan parámetros como tag_id en el export?
class ProductProduct(models.Model):
    _inherit = 'product.product'

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def export_product_tag_rel(self):
        # product_tag_rel_exporter = _get_exporter(session, model_name, product_record_id,
        #                                          ProductTagRelExporter)
        # return product_tag_rel_exporter.update(product_record_id, tag_record_id, "insert")
        return True

    @job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
    def unlink_product_tag_rel(self):
        # product_tag_rel_exporter = _get_exporter(session, model_name, product_record_id,
        #                                          ProductTagRelExporter)
        # return product_tag_rel_exporter.delete(product_record_id)
        return True
