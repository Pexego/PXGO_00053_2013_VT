from odoo import api, fields, models, tools, _


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _get_partner_pricelist_multi_2(self, partner_ids, company_id=None):
        Partner = self.env['res.partner']
        Property = self.env['ir.property'].with_context(force_company=company_id or self.env.user.company_id.id)

        # retrieve values of property
        result = Property.get_multi('property_product_pricelist', Partner._name, partner_ids)

        return result
