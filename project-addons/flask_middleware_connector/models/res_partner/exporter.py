# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component


class ResPartnerExporter(Component):
    _name = 'res.partner.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['res.partner']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {
            "is_company": binding.is_company,
            "fiscal_name": binding.name,
            "commercial_name": binding.comercial or "",
            "odoo_id": binding.id,
            "vat": binding.vat or "",
            "street": binding.street or "",
            "city": binding.city or "",
            "zipcode": binding.zip,
            "commercial_id": binding.user_id.id,
            "country": binding.country_id and binding.country_id.code or
            "",
            "ref": binding.ref,
            "discount": binding.discount,
            "pricelist_name": binding.property_product_pricelist and
            binding.property_product_pricelist.name or "",
            "state": binding.state_id and binding.state_id.name or "",
            "email": binding.email_web or "",
            "email_sat": binding.email3 or "",
            "prospective": binding.prospective,
            "lang": binding.lang and binding.lang.split("_")[0] or 'es',
            "phone1": binding.phone,
            "phone2": binding.mobile,
            "is_prepaid_payment_term":  binding.prepaid_payment_term(),
            "last_sale_date": binding.last_sale_date,
            "csv_connector_access": binding.csv_connector_access,
            "brand_pricelist_ids": f'{binding.pricelist_brand_ids.ids or ""}',
            "tag_ids": f'{binding.category_id.ids or ""}',
            "zone": binding.area_id.name
        }
        if not vals['is_company'] and binding.parent_id:
            vals.update({"type": binding.type, "parent_id": binding.parent_id.id, "email": binding.email})
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)

class ResPartnerAdapter(Component):

    _name = 'res.partner.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'res.partner'
    _middleware_model = 'customer'


class ResPartnerCategoryExporter(Component):
    _name = 'res.partner.category.exporter'
    _inherit = ['base.exporter']
    _apply_on = ['res.partner.category']
    _usage = 'record.exporter'

    def update(self, binding, mode):
        vals = {
            "odoo_id": binding.id,
            "name": binding.name or "",
            "parent_id": binding.parent_id.id,
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding.id, vals)

    def delete(self, binding):
        return self.backend_adapter.remove(binding.id)


class ResPartnerCategoryAdapter(Component):

    _name = 'res.partner.category.general.adapter'
    _inherit = 'middleware.adapter'
    _apply_on = 'res.partner.category'
    _middleware_model = 'customertag'
