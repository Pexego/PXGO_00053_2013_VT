# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
import datetime

class ProductProductExporter(Component):
    _name = 'product.product.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['product.product']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {
            'name': binding.name,
            'code': binding.default_code,
            'odoo_id': binding.id,
            'categ_id': binding.categ_id.id,
            'pvi_1': binding.get_product_price_with_pricelist('PVIIberia'),
            'pvi_2': binding.get_product_price_with_pricelist('PVIEuropa'),
            'pvi_3': binding.get_product_price_with_pricelist('PVIItalia'),
            'pvi_4': binding.get_product_price_with_pricelist('PVIFrancia'),
            'uom_name': binding.uom_id.name,
            'last_sixty_days_sales': binding.last_sixty_days_sales,
            'brand_id': binding.product_brand_id.id,
            'pvd_1': binding.get_product_price_with_pricelist('PVDIberia'),
            'pvd_2': binding.get_product_price_with_pricelist('PVDEuropa'),
            'pvd_3': binding.get_product_price_with_pricelist('PVDItalia'),
            'pvd_4': binding.get_product_price_with_pricelist('PVDFrancia'),
            'pvm_1': binding.get_product_price_with_pricelist('PVMA'),
            'pvm_2': binding.get_product_price_with_pricelist('PVMB'),
            'pvm_3': binding.get_product_price_with_pricelist('PVMC'),
            'joking_index': binding.joking_index,
            'sale_ok': binding.sale_ok,
            'ean13': binding.barcode,
            'manufacturer_ref': binding.manufacturer_pref,
            'description_sale': binding.description_sale,
            'type': binding.type,
            'is_pack': binding.is_pack,
            'discontinued': binding.discontinued,
            'state': binding.state,
            'sale_in_groups_of': binding.sale_in_groups_of,
            'replacement_id': binding.replacement_id.id,
            'final_replacement_id': binding.final_replacement_id.id,
            'date_next_incoming': binding.date_next_incoming if binding.date_next_incoming else (
                    datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S"),
            'weight': binding.weight,
            'volume': binding.volume,
            'cost_price': binding.standard_price_2_inc,
            'real_stock': binding.qty_available,
            'special_shipping_costs': binding.special_shipping_costs,
            "tag_ids": f'{binding.tag_ids.ids or ""}',
            'equivalent_products':  str(binding.equivalent_product_ids.mapped("product_name"))
        }
        if binding.show_stock_outside:
            stock_qty = eval(
                "product." + self.backend_record.product_stock_field_id.name,
                {'product': binding})
            vals["stock"] = stock_qty
        country_code = self.env.user.company_id.country_id.code
        if country_code == "IT":
            vals['stock_available_es'] = binding.virtual_stock_conservative_es
        if mode == "insert":
            self.backend_adapter.insert(vals)
        else:
            self.backend_adapter.update(binding.id, vals)
        return True

    def delete(self, binding):
        self.backend_adapter.remove(binding.id)
        return True

class ProductProductAdapter(Component):
    _name = 'product.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'product.product'
    _middleware_model = 'product'


class ProductCategoryExporter(Component):
    _name = 'product.category.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['product.category']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {"name": binding.with_context({'lang': 'es_ES'}).name,
                "parent_id": binding.parent_id.id,
                "odoo_id": binding.id
                }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class ProductCategoryAdapter(Component):
    _name = 'productcategory.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'product.category'
    _middleware_model = 'productcategory'


class ProductBrandExporter(Component):
    _name = 'product.brand.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['product.brand']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {"name": binding.name,
                "odoo_id": binding.id,
                "no_csv": binding.no_csv,
                "group_id": binding.group_brand_id.id}
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class ProductBrandAdapter(Component):
    _name = 'productbrand.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'product.brand'
    _middleware_model = 'productbrand'


class ProductbrandRelExporter(Component):
    _name = 'brand.country.rel.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['brand.country.rel']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {
            "country_id": binding.country_id.id,
            "brand_id": binding.brand_id.id,
            "odoo_id": binding.id
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class ProductbrandRelAdapter(Component):
    _name = 'productbrandcountryrel.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'brand.country.rel'
    _middleware_model = 'productbrandcountryrel'


class ProductTagExporter(Component):
    _name = 'product.tag.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['product.tag']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {
            "odoo_id": binding.id,
            "name": binding.name,
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class ProductTagAdapter(Component):
    _name = 'producttag.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'product.tag'
    _middleware_model = 'producttag'

class ProductBrandGroupExporter(Component):
    _name = 'product.brand.group.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['brand.group']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {"name": binding.name,
                "odoo_id": binding.id
                }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class ProductBrandGroupAdapter(Component):
    _name = 'productbrandgroup.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'brand.group'
    _middleware_model = 'productbrandgroup'
