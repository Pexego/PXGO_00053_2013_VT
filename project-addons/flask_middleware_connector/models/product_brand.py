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
from odoo import models, fields, api, exceptions, _


class ProductBrand(models.Model):

    _inherit = 'product.brand'

    '''country_ids = fields.One2Many(
        'res.country',
        'brand_country_rel',
        'brand_id',
        'country_id',
        'Countries')'''

    country_ids = fields.One2many('brand.country.rel', 'brand_id', 'Countries')


class BrandCountryRel(models.Model):

    _name = 'brand.country.rel'

    brand_id = fields.Many2one('product.brand', 'Brand')
    country_id = fields.Many2one('res.country', 'Country')
