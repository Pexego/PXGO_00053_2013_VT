# -*- coding: utf-8 -*-
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
from openerp import models, fields, api, exceptions, _
from datetime import datetime

class StockTransferDetails(models.TransientModel):

    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        if self.picking_id.claim_id:
            if self.picking_id.picking_type_code == 'incoming':
                field = 'date_in'
            else:
                field = 'date_out'
            products = [x.product_id.id for x in self.item_ids]
            for claim_line in self.picking_id.claim_id.claim_line_ids:
                if claim_line.product_id.id in products:
                    claim_line[field] = datetime.now()
        return super(StockTransferDetails, self).do_detailed_transfer()
