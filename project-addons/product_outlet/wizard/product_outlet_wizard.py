# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
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


class product_outlet_wizard(models.TransientModel):

    _name = "product.outlet.wizard"

    qty = fields.Float(
        'Quantity',
        default=lambda self: self.env['product.product'].browse(
            self.env.context.get('active_id', False)).qty_available)
    product_id = fields.Many2one('product.product', 'Product',
                                 default=lambda self:
                                 self.env.context.get('active_id', False))

    @api.multi
    def make_move(self):
        outlet_categ_id = self.env.ref('product_outlet.product_category_outlet')
        stock_location = self.env.ref('stock.stock_location_stock')
        outlet_location = self.env.ref('product_outlet.stock_location_outlet')
        stock_change_qty_obj = self.env['stock.change.product.qty']
        if self.qty > self.product_id.qty_available:
            raise exceptions.except_orm(
                _('Quantity error'),
                _('the amount entered is greater than the quantity available.'))

        if self.product_id.categ_id == outlet_categ_id:
            raise exceptions.except_orm(
                _('product error'),
                _('This product is in outlet category.'))

        # todo el producto pasa a outlet.
        if self.qty == self.product_id.virtual_available:
            self.product_id.categ_id = outlet_categ_id
            new_product = self.product_id

        # Alguna cantidad se mantiene en stock.
        else:
            # crear nuevo producto
            if not self.product_id.outlet_product_id:
                new_product = self.product_id.copy(
                    {'categ_id': outlet_categ_id.id,
                     'name': self.product_id.name + u' Outlet',
                     'image_medium': self.product_id.image_medium})
                self.product_id.outlet_product_id = new_product.id
            else:
                new_product = self.product_id.outlet_product_id
        stock_change_qty_obj.create(
            {'product_id': self.product_id.id,
             'new_quantity': self.product_id.qty_available - self.qty,
             'location_id': stock_location.id}).change_product_qty()

        stock_change_qty_obj.create({'product_id': new_product.id,
                                     'new_quantity': new_product.qty_available + self.qty,
                                     'location_id': outlet_location.id}).change_product_qty()
        return {'type': 'ir.actions.act_window_close'}
