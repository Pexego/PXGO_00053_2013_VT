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



class product_devaluation_wizard(models.TransientModel):

    _name= 'product.devaluation.wizard'


    #product_id = fields.Integer(
    product_id = fields.Many2one('product.product',
        'Product',
        default=lambda self: self.env['product.product'].browse(
            self.env.context.get('active_id', False)), readonly=True)

    price_before = fields.Float(
        'Price Before',
        default=lambda self: self.env['product.product'].browse(
            self.env.context.get('active_id', False)).standard_price, readonly=True)

    price_after = fields.Float(
        'Price After', required=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).standard_price)

    date_dev = fields.Date('Date', default=fields.Date.today, required=True)



    @api.multi
    def create_dev(self):
        values = {
                'quantity': self.product_id.qty_available,
                'price_before': self.price_before,
                'price_after': self.price_after,
                'product_id': self.product_id.id,
                'date_dev': self.date_dev,
        }
        self.env['product.devaluation'].create(values)
        values = {
                'standard_price' : self.price_after,
                }
        self.env['product.product'].search([('id','=',self.product_id.id)]).write(values)
