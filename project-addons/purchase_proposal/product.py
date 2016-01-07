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


class ProductProduct(models.Model):

    _inherit = 'product.product'

    last_sixty_days_sales = fields.Float('Sales in last 60 days with stock',
                                         readonly=True)
    joking_index = fields.Float("Joking index", readonly=True)
    order_cycle = fields.Integer('Order cycle')
    transport_time = fields.Integer('Transport time')
    security_margin = fields.Integer('Security margin')

    @api.model
    def compute_last_sixty_days_sales(self):
        positive_days_obj = self.env['stock.days.positive']
        move_obj = self.env['stock.move']
        for product in self.search([('type', '!=', 'service')]):
            days = positive_days_obj.search([('product_id', '=', product.id)],
                                            limit=60, order='datum desc')
            if not days:
                product.last_sixty_days_sales = 0
                continue
            moves = move_obj.search([('date', '>=', days[-1].datum),
                                     ('state', '=', 'done'),
                                     ('product_id', '=', product.id),
                                     ('picking_type_id.code', '=',
                                      'outgoing')])
            product.last_sixty_days_sales = sum(
                [x.product_uom_qty for x in moves
                 if x.procurement_id.sale_line_id])
            product.joking_index = product.last_sixty_days_sales * \
                product.standard_price
