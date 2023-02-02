# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component
import datetime

class ProductPricelistExporter(Component):
    _name = 'product.pricelist.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['product.pricelist']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {
            'name': binding.name,
            'brand_group_id': binding.brand_group_id.id or False,
            'odoo_id': binding.id
        }
        if mode == "insert":
            self.backend_adapter.insert(vals)
        else:
            self.backend_adapter.update(binding.id, vals)
        return True

    def delete(self, binding):
        self.backend_adapter.remove(binding.id)
        return True


class ProductPricelistAdapter(Component):
    _name = 'product.pricelist.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'product.pricelist'
    _middleware_model = 'productpricelist'


class ProductPricelistItemExporter(Component):
    _name = 'product.pricelist.item.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['product.pricelist.item']
    _usage = 'record.exporter'

    def update(self, binding, mode, product):
        pricelist = binding.pricelist_calculated if binding.item_id and binding.pricelist_calculated else binding.pricelist_id

        id = int(f'{product.id}{pricelist.id}')
        vals = {
            'name': f'{product.default_code}-{pricelist.name}',
            'product_id': product.id,
            'pricelist_id': pricelist.id,
            'odoo_id':id,
            'price': pricelist._compute_price_rule([(product,1,False)], date=False, uom_id=False)[product.id][0]
        }
        if mode == "insert":
            self.backend_adapter.insert(vals)
        else:
            self.backend_adapter.update(id, vals)
        return True

    def delete(self, binding,product):
        pricelist = binding.pricelist_calculated.id if binding.item_id and binding.pricelist_calculated else binding.pricelist_id
        id = int(f'{product.id}{pricelist.id}')
        self.backend_adapter.remove(id)
        return True


class ProductPricelistItemAdapter(Component):
    _name = 'product.pricelist.item.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'product.pricelist.item'
    _middleware_model = 'productpricelistitem'
