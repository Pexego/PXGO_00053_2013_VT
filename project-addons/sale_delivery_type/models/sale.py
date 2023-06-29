##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
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

from odoo import models, api, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_type = fields.Selection([
            ('shipping', 'Shipping'),
            ('carrier', 'Carrier - Customer'),
            ('installations', 'Pickup in installations')],
            'Delivery type', required=True, default='shipping')

    @api.onchange('delivery_type')
    @api.multi
    def onchange_delivery_type(self):
        carrier_to_set = False
        transporter_to_set = False

        if self.delivery_type == 'installations':
            carrierServ_id = self.env.ref('delivery_carrier_custom.delivery_carrier_carrier')
            carrier_to_set = carrierServ_id.id
            transporter_to_set = carrierServ_id.partner_id.id

        elif self.delivery_type == 'carrier':
            installationServ_id = self.env.ref('delivery_carrier_custom.delivery_carrier_installations')
            carrier_to_set = installationServ_id.id
            transporter_to_set = installationServ_id.partner_id.id

        elif self.delivery_type == 'shipping':
            carrier_to_set = self.partner_id.property_delivery_carrier_id.id
            transporter_to_set = self.partner_id.transporter_id.id

        self.carrier_id = carrier_to_set
        self.transporter_id = transporter_to_set
