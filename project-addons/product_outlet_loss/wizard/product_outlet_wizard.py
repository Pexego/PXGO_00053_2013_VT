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

    #~ price_unit = fields.Float(
        #~ 'Price Before',
        #~ default=lambda self: self.env['product.product'].browse(
            #~ self.env.context.get('active_id', False)).standard_price, Readonly=True)
#~
    #~ price_outlet = fields.Float(
        #~ 'Price After',
        #~ default=lambda self:
        #~ self.env['product.product'].browse(self.env.context.get('active_id', False)).standard_price *
        #~ (100 - self.env['product.product'].browse(self.env.context.get('active_id', False)).company_id.outlet_per_cent)
        #~ / 100)

    list_price2 = fields.Float(
        'Price PVP 2',
        readonly=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).list_price2)

    list_price = fields.Float(
        'Price PVP',
        readonly=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).list_price)

    list_price3 = fields.Float(
        'Price PVP 3',
        readonly=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).list_price3)

    commercial_cost = fields.Float(
        'Commercial Cost',
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).commercial_cost)

    percent = fields.Char('Default Outlet Price in %', default=lambda self: self.env['product.product'].browse(
        self.env.context.get('active_id', False)).company_id.outlet_per_cent, Readonly=True)

    qty_available = fields.Float(
        'Qty from stock',
        default=lambda self: self.env['product.product'].browse(
            self.env.context.get('active_id', False)).qty_available, Readonly=True)

    date_move = fields.Date('Move to outlet on', default=fields.datetime.now())

    @api.multi
    def make_move(self):
        product = self.product_id
        outlet_id = product.id
        act_prod = False
        create_loss = False
        outlet_product_selected = []

        if self.state == "first":
            res = super(product_outlet_wizard, self).make_move()
        else:
            if self.qty_available < self.qty:
                raise ValidationError(_("Qty to outlet must be <= qty available"))
            if self.qty <= 0:
                raise ValidationError(_("Qty to outlet must be >=0"))
            category_selected = self.env['product.category'].browse(int(self.categ_id))
            outlet_product_selected = self.env['product.product'].search(
                [('default_code', '=', self.product_id.name + category_selected.name)]
            )

            res = super(product_outlet_wizard, self).make_move()

            if self.state == "last":
                act_prod = True
                create_loss = True
                price_outlet = self.list_price - (self.list_price *
                                                  (category_selected.percent / 100))

                price_outlet2 = self.list_price2 - (self.list_price2 *
                                                    (category_selected.percent / 100))

                price_outlet3 = self.list_price3 - (self.list_price3 *
                                                    (category_selected.percent / 100))

        outlet_product = self.env['product.product'].search(
            [('normal_product_id', '=', self.product_id.id), ('categ_id', '=', int(self.categ_id))])

        if create_loss:
            if not outlet_product_selected:
                values = {
                    'qty': self.qty,
                    'price_outlet': price_outlet,
                    'price_unit': price_outlet,
                    'product_id': outlet_product.id,
                    'date_move': self.date_move,
                    'outlet_ok': True
                }
                self.env['outlet.loss'].create(values)
            else:
                values = {
                    'qty': self.qty,
                    'product_id': outlet_product.id,
                    'date_move': self.date_move,
                    'outlet_ok': True
                }
                self.env['outlet.loss'].create(values)

        if act_prod:
            if not outlet_product_selected:
                values = {
                    'standard_price': price_outlet,
                    'list_price2': price_outlet2,
                    'list_price3': price_outlet3,
                    'commercial_cost': self.commercial_cost,
                    'list_price': price_outlet
                }
                outlet_product.write(values)

        return res
