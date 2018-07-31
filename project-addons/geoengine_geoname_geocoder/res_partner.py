# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2011-2012 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
# TODO create a base Geocoder module
from urllib import urlencode
from urllib2 import urlopen
import xml.dom.minidom
import logging
import unidecode

from openerp import fields as fields2, models, api, _
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
from openerp.exceptions import except_orm

from openerp.addons.base_geoengine import geo_model, fields

logger = logging.getLogger('GeoNames address encoding')


class ResPartner(geo_model.GeoModel):
    """Auto geo coding of addresses"""
    _inherit = "res.partner"

    geo_point = fields.GeoPoint(
        'Addresses coordinate', readonly=True)
    addr_accuracy = fields2.Char('Address Accuracy', readonly=True)

    def _can_geocode(self):
        usr = self.env['res.users']
        return usr.browse(self.env.uid).company_id.enable_geocoding

    def _get_point_from_reply(self, answer):
        """Parse geoname answer code inspired by geopy library"""

        def get_first_text(node, tag_names, strip=None):
            """Get the text value of the first child of ``node`` with tag
            ``tag_name``. The text is stripped using the value of ``strip``."""
            if isinstance(tag_names, basestring):
                tag_names = [tag_names]
            if node:
                while tag_names:
                    nodes = node.getElementsByTagName(tag_names.pop(0))
                    if nodes:
                        child = nodes[0].firstChild
                        return child and child.nodeValue.strip(strip)

        def parse_code(code):
            latitude = get_first_text(code, 'lat') or None
            longitude = get_first_text(code, 'lng') or None
            latitude = latitude and float(latitude)
            longitude = longitude and float(longitude)
            accuracy = get_first_text(code, 'location_type') or 'PRECISE'
            return latitude, longitude, accuracy

        res = answer.read()
        if not isinstance(res, basestring):
            return False
        doc = xml.dom.minidom.parseString(res)
        codes = doc.getElementsByTagName('result')
        if len(codes) < 1:
            logger.warn("Geonaming failed: %s", res)
            return False
        for code in codes:
            address = get_first_text(code, 'formatted_address')
            if self.country_id.name in address:
                latitude, longitude, accuracy = parse_code(code)
            else:
                latitude = False
                longitude = False
        if not latitude or not longitude:
            latitude, longitude, accuracy = parse_code(codes[0])
        if accuracy != 'APPROXIMATE':
            accuracy = 'PRECISE'
        self.addr_accuracy = accuracy
        return fields.GeoPoint.from_latlon(self.env.cr, latitude, longitude)

    @api.multi
    def geocode_from_geonames(self, strict=True, context=None):
        base_url = u'https://maps.googleapis.com/maps/api/geocode/xml?address='
        API_KEY = self.env['ir.config_parameter'].get_param('google.maps.api')
        for partner in self:
            logger.info('geolocalizing %s', partner.name)
            address = ''
            if partner.street:
                address += unidecode.unidecode(partner.street)
            elif partner.parent_id and partner.parent_id.street:
                address += unidecode.unidecode(partner.parent_id.street)
            if partner.city:
                address += '+' + unidecode.unidecode(partner.city)
            elif partner.parent_id and partner.parent_id.city:
                address += unidecode.unidecode(partner.parent_id.city)
            if partner.country_id.name:
                address += '+' + unidecode.unidecode(partner.country_id.name)
            elif partner.parent_id and partner.parent_id.country_id.name:
                address += '+' + unidecode.unidecode(partner.parent_id.country_id.name)

            address = address.replace(' ', '+')
            # address = unidecode.unidecode(address)

            url = base_url + address + '&key=' + API_KEY
            try:
                answer = urlopen(url)
                partner.geo_point = self._get_point_from_reply(answer)
            except:
                logger.info('error - %s ', partner.name)
                logger.info('%s - %s, %s', partner.name, partner.street, partner.city)

    @api.multi
    def geocode_partner(self):

        # TODO: se podría llamar a la función de arriba ya que hace lo mismo

        base_url = u'https://maps.googleapis.com/maps/api/geocode/xml?address='
        API_KEY = self.env['ir.config_parameter'].get_param('google.maps.api')
        for partner in self:
            logger.info('geolocalizing %s', partner.name)
            address = ''
            if partner.street:
                address += unidecode.unidecode(partner.street)
            elif partner.parent_id and partner.parent_id.street:
                address += unidecode.unidecode(partner.parent_id.street)
            if partner.city:
                address += '+' + unidecode.unidecode(partner.city)
            elif partner.parent_id and partner.parent_id.city:
                address += unidecode.unidecode(partner.parent_id.city)
            if partner.country_id.name:
                address += '+' + unidecode.unidecode(partner.country_id.name)
            elif partner.parent_id and partner.parent_id.country_id.name:
                address += '+' + unidecode.unidecode(partner.parent_id.country_id.name)

            address = address.replace(' ', '+')
            # address = unidecode.unidecode(address)

            url = base_url + address + '&key=' + API_KEY
            try:
                answer = urlopen(url)
                partner.geo_point = self._get_point_from_reply(answer)
            except:
                logger.info('error - %s ', partner.name)
                logger.info('%s - %s, %s', partner.name, partner.street, partner.city)

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        do_geocode = self._can_geocode()
        if do_geocode and \
                set(('country_id', 'city', 'zip')).intersection(vals):
            self.geocode_from_geonames()
        return res

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        do_geocode = self._can_geocode()
        if do_geocode:
            res.geocode_from_geonames()
        return res
