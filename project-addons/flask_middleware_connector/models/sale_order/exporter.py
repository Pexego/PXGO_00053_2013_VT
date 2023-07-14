# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class SaleOrderExporter(Component):
    _name = 'sale.order.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['sale.order']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        state = binding.state
        if state in ('shipping_except', 'invoice_except'):
            state = 'done'
        vals = {
            "odoo_id": binding.id,
            "name": binding.name,
            "state": state,
            "partner_id": binding.partner_id.id,
            "amount_total": binding.amount_total,
            "date_order": binding.date_order,
            "amount_untaxed": binding.amount_untaxed,
            "client_order_ref": binding.client_order_ref,
            'shipping_street': binding.partner_shipping_id.street,
            'shipping_zip': binding.partner_shipping_id.zip,
            'shipping_city': binding.partner_shipping_id.city,
            'shipping_state': binding.partner_shipping_id.state_id.name,
            'shipping_country': binding.partner_shipping_id.country_id.name,
            'delivery_type': binding.delivery_type,
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class SaleOrderAdapter(Component):

    _name = 'order.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'sale.order'
    _middleware_model = 'order'


class SaleOrderLineExporter(Component):
    _name = 'sale.order.line.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['sale.order.line']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {"odoo_id": binding.id,
                "product_id": binding.product_id.id,
                "product_qty": binding.product_uom_qty,
                "price_subtotal": binding.price_subtotal,
                "order_id": binding.order_id.id,
                "no_rappel": binding.no_rappel,
                "deposit": binding.deposit,
                "discount": binding.discount,
                "price_unit": binding.price_unit,
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class SaleOrderLineAdapter(Component):

    _name = 'orderproduct.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'sale.order.line'
    _middleware_model = 'orderproduct'
