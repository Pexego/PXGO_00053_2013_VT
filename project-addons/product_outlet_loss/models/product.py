##############################################################################
#
#    Copyright (C) 2014 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sánchez <kiko@comunitea.com>$
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

from odoo import fields, models, api
from datetime import datetime


class OutletLoss(models.Model):

    _name = 'outlet.loss'

    @api.multi
    @api.depends('qty', 'price_outlet', 'price_unit')
    def _get_outlet_loss(self):
        for loss in self:
            loss.total_lost = loss.qty*(loss.price_outlet-loss.price_unit)

    product_id = fields.Many2one('product.product', 'Product')
    price_unit = fields.Float('Price')
    price_outlet = fields.Float('Outlet Price')
    total_lost = fields.Float("Outlet Loss", compute=_get_outlet_loss,
                              store=True, readonly=True)
    date_move = fields.Date('Move to outlet on', default=fields.datetime.now())
    outlet_ok = fields.Boolean('Outlet')
    order_line_id = fields.Many2one('sale.order.line', 'Order Line')
    qty = fields.Float('Quantity')
    percent = fields.Float('Outlet Percent')



