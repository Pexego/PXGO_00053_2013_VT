# -*- coding: utf-8 -*-
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
import openerp
from openerp.osv import osv, fields
from openerp import models, api


class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'delivery_type': fields.selection([
            ('shipping', 'Shipping'),
            ('carrier', 'Carrier - Customer'),
            ('installations', 'Pickup in installations'), ],
            'Delivery type', required=True)
    }
    _defaults = {
        'delivery_type': 'shipping'
    }

    @api.onchange('delivery_type')
    def onchange_delivery_type(self):
        carrierServ_id = self.env['transportation.service'].search([('name', '=', 'Medios Propios')]).ids
        carrierTrans_id = self.env['transportation.transporter'].search([('name', '=', 'Medios Propios')]).ids
        installationServ_id = self.env['transportation.service'].search([('name', '=', 'Recoge agencia cliente')]).ids
        installationTrans_id = self.env['transportation.transporter'].search([('name', '=', 'Recoge agencia cliente')]).ids

        if self.delivery_type == 'installations':
            self.service_id = carrierServ_id[0]
            self.transporter_id = carrierTrans_id[0]

        if self.delivery_type == 'carrier':
            self.service_id = installationServ_id[0]
            self.transporter_id = installationTrans_id[0]

        if self.delivery_type == 'shipping':
            self.service_id = self.partner_id.service_id.id
            self.transporter_id = self.partner_id.transporter_id.id


