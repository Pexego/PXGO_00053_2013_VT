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
from openerp import models, fields, api


class res_partner(models.Model):

    _inherit = 'res.partner'

    shipment_bag_ids = fields.One2many('shipment.bag', 'partner_id',
                                       'Shipments')
    shipment_count = fields.Float('shipments', compute='_get_shipment_count')

    @api.multi
    @api.depends('shipment_bag_ids')
    def _get_shipment_count(self):
        for partner in self:
            partner.shipment_count = len(partner.shipment_bag_ids)
