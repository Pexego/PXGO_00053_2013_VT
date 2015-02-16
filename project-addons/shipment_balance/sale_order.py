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


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    shipment_added = fields.Boolean('Shipment added')

    @api.one
    def use_paid_shipment(self):
        if self.shipment_added:
            return
        shipping = self.env['shipment.bag'].search([('partner_id', '=', self.partner_id.id)])
        if shipping:
            shipping[0].active = False
            self.shipment_added = True
        else:
            raise exceptions.Warning(_('Shipment error'), _('Not shipments paid founded'))
