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
    all_product = fields.Boolean('Move all to outlet.')
    # categ_id = fields.Many2one('product.category', 'Category')
    categ_id = fields.Selection(selection='_get_outlet_categories',
                                string='category')
    state = fields.Selection([('first', 'First'), ('last', 'Last')],
                             default='first')

    @api.model
    def _get_outlet_categories(self):
        res = []
        outlet_categ_id = self.env.ref('product_outlet.product_category_outlet')
        for categ in outlet_categ_id.child_id:
            res.append((categ.id, categ.name))
        return res

    @api.multi
    def make_move(self):
        outlet_categ_id = self.env.ref('product_outlet.product_category_outlet')
        stock_location = self.env.ref('stock.stock_location_stock')
        outlet_location = self.env.ref('product_outlet.stock_location_outlet')
        stock_change_qty_obj = self.env['stock.change.product.qty']
        categ_obj = self.env['product.category']
        outlet_tag = self.env.ref('product_outlet.tag_outlet')
        # mover toda la cantidad
        if self.all_product:
            self.product_id.categ_id = outlet_categ_id
            new_product = self.product_id
            new_product.write({'tag_ids': [(4,outlet_tag.id)]})

        else:
            if self.state == 'first':
                self.state = 'last'
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'product.outlet.wizard',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_id': self.id,
                    'views': [(False, 'form')],
                    'target': 'new',
                }
            ctx = dict(self.env.context)
            ctx['location'] = stock_location.id
            product = self.env['product.product'].\
                with_context(ctx).browse(self.product_id.id)
            if self.qty > product.qty_available:
                raise exceptions.except_orm(
                    _('Quantity error'),
                    _('the amount entered is greater than the quantity '
                      'available in stock.'))
            if product.categ_id == outlet_categ_id or \
                    product.categ_id.parent_id == outlet_categ_id:
                raise exceptions.except_orm(
                    _('product error'),
                    _('This product is already in outlet category.'))

            # crear nuevo producto
            outlet_product = self.env['product.product'].search(
                [('normal_product_id', '=', product.id),
                 ('categ_id', '=', int(self.categ_id))])
            if not outlet_product:
                new_product = product.copy(
                    {'categ_id': int(self.categ_id),
                     'name': product.name + u' ' +
                     categ_obj.browse(int(self.categ_id)).name,
                     'default_code': product.default_code +
                     categ_obj.browse(int(self.categ_id)).name,
                     'image_medium': product.image_medium})
                categ = self.env['product.category'].browse(int(self.categ_id))
                tag = self.env['product.tag'].search([('name', '=',
                                                       categ.name)])
                if not tag:
                    outlet_tag = self.env.ref('product_outlet.tag_outlet')
                    tag = self.env['product.tag'].create(
                        {'name': categ.name, 'parent_id': outlet_tag.id})
                new_product.write({'tag_ids': [(4, tag.id)]})
                new_product.normal_product_id = self.product_id
            else:
                new_product = outlet_product
            new_product = self.env['product.product'].\
                with_context(ctx).browse(new_product.id)
            stock_change_qty_obj.create(
                {'product_id': product.id,
                 'new_quantity': product.qty_available - self.qty,
                 'location_id': stock_location.id}).change_product_qty()

            stock_change_qty_obj.create({'product_id': new_product.id,
                                         'new_quantity': new_product.qty_available + self.qty,
                                         'location_id': outlet_location.id}).change_product_qty()
        return {'type': 'ir.actions.act_window_close'}
