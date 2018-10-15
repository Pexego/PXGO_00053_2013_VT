##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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

from odoo import models, fields, api
from odoo import modules
import base64


class res_partner(models.Model):
    _inherit = 'res.partner'

    area_id = fields.Many2one('res.partner.area', 'Area')
    region_ids = fields.Many2many(related='area_id.commercial_region_ids')
    default_shipping_address = fields.Boolean('Default Shipping Address', default=False)

    @api.onchange('default_shipping_address')
    def onchange_default_shipping(self):
        if self.default_shipping_address:
            image = modules.get_module_resource('customer_area', 'static/src/img/', 'icon-fav.png')
            with open(image, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
                self.image = encoded_string
        else:
            self.image = False

    @api.multi
    def change_sales_team(self, area_id):
        area = self.env['res.partner.area'].browse(int(area_id))

        return {'value': {'section_id': area.sales_team.id}}


class res_partner_area(models.Model):
    _name = "res.partner.area"

    name = fields.Char('Name', size=64, required=True)
    code = fields.Char('Code', size=15)
    sales_team = fields.Many2one('crm.team', 'Sales Team')
    commercial_region_ids = fields.Many2many('res.partner.area.region', 'res_partner_area_region_rel',
                                             'area_id', 'commercial_region_id', 'Commercial Regions')


class res_partner_area_region(models.Model):
    _name = "res.partner.area.region"
    _description = "Commercial Region"

    name = fields.Char('Name', size=64, required=True)
    code = fields.Char('Code', size=15)
    area_ids = fields.Many2many('res.partner.area', 'res_partner_area_region_rel',
                                'commercial_region_id', 'area_id', 'Areas')


