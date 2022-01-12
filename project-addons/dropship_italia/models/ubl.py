from odoo import models, api


class BaseUbl(models.AbstractModel):
    _inherit = 'base.ubl'

    @api.model
    def ubl_parse_address(self, address_node, ns):
        res = super().ubl_parse_address(address_node, ns)
        street_xpath = address_node.xpath(
            'cbc:StreetName', namespaces=ns)
        street = street_xpath and street_xpath[0].text or False
        city_xpath = address_node.xpath(
            'cbc:CityName', namespaces=ns)
        city = city_xpath and city_xpath[0].text or False
        state_xpath = address_node.xpath(
            'cbc:CountrySubentity', namespaces=ns)
        state_name = state_xpath and state_xpath[0].text or False
        state = self.env['res.country.state'].search([('name', '=', state_name)])
        # TODO: filtrar por pais también.

        address_dict = {
            'street': street,
            'city': city,
            'state_id': state.id
        }
        res.update(address_dict)
        return res