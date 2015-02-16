# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
from openerp import models, fields, api, exceptions, _
from datetime import date


class CrmClaim(models.Model):

    _inherit = 'crm.claim'

    shipment_paid = fields.Boolean('Shipment paid')

    @api.one
    def customer_paid_shipping(self):
        shipment_dict = {
            'partner_id': self.partner_id.id,
            'date': date.today(),
            'active': True,
            'origin': self.name
        }
        self.env['shipment.bag'].create(shipment_dict)
        self.shipment_paid = True
