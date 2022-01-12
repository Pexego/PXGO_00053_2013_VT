from odoo import models, api


class BusinessDocumentImport(models.AbstractModel):
    _inherit = 'business.document.import'

    @api.model
    def _match_shipping_partner(self, shipping_dict, partner, chatter_msg):
        if shipping_dict.get('partner'):
            if self.env.context.get('dropship_sale', False):
                partner_vals = shipping_dict.get('partner')
                address_vals = shipping_dict.get('address')
                if partner_vals['name'] != 'VISIOTECH Italia':
                    p_it = self.env['res.partner'].search([('name', '=', 'VISIOTECH Italia'),
                                                           ('is_company', '=', True)]).id
                    partner = self.env['res.partner'].search([('name', '=', partner_vals['name']),
                                                              ('dropship', '=', True),
                                                              ('parent_id', '=', p_it),
                                                              ('type', '=', 'delivery')])
                    if not partner:
                        partner_vals['dropship'] = True
                        partner_vals['active'] = False
                        partner_vals['email'] = False
                        partner_vals['country_id'] = self.env['res.country'].search([('code', '=', partner_vals['country_code'])]).id
                        partner_vals.pop('country_code')
                        partner_vals.pop('state_code')
                        partner_vals['customer'] = True
                        partner_vals['is_company'] = False
                        partner_vals['delivery_type'] = 'shipping'
                        partner_vals['parent_id'] = p_it
                        partner_vals['type'] = 'delivery'
                        # Delivery address
                        partner_vals['street'] = address_vals['street']
                        partner_vals['city'] = address_vals['city']
                        partner_vals['zip'] = address_vals['zip']
                        partner_vals['state_id'] = address_vals['state_id']
                        partner = self.env['res.partner'].create(partner_vals)
                        return partner

        return super()._match_shipping_partner(shipping_dict, partner, chatter_msg)
