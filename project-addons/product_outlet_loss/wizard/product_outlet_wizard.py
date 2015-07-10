# -*- coding: utf-8 -*-
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

from openerp import models, fields, api, exceptions, _
from datetime import datetime, time
from openerp.exceptions import ValidationError



class product_outlet_wizard(models.TransientModel):

    _inherit = 'product.outlet.wizard'
    price_outlet = fields.Float(
        'Outlet Price',
        default=lambda self: self.env['product.product'].browse(
            self.env.context.get('active_id', False)).list_price2)

    price_unit = fields.Float(
        'Price',
        default=lambda self: self.env['product.product'].browse(
            self.env.context.get('active_id', False)).list_price2, Readonly=True)

    qty_available = fields.Float(
        'Qty from stock',
        default=lambda self: self.env['product.product'].browse(
            self.env.context.get('active_id', False)).qty_available, Readonly=True)

    date_move = fields.Date('Move to outlet on', default = fields.datetime.now())


    @api.multi
    def make_move(self):
        last = self.state
        if self.qty_available < self.qty:
            raise ValidationError("Qty to outlet must be <= qty available")

        if self.qty <= 0:
            raise ValidationError("Qty to outlet must be >=0")

        res = super(product_outlet_wizard, self).make_move()
        if last == "last":
            price_unit=  self.env['product.product'].search([('id', '=', self.product_id.id)]).list_price2
            values = {
                'qty' :self.qty,
                'price_outlet' : self.price_outlet,
                'price_unit' : price_unit,
                'product_id' : self.product_id.id,
                'date_move' : self.date_move
            }
            self.env['outlet.loss'].create (values)
        return res

