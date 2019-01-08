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

from odoo import models, fields, api, exceptions, _
from datetime import datetime, time
from odoo.exceptions import ValidationError

class ProductOutletWizard(models.TransientModel):
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

    lst_price = fields.Float(
        'Price PVP',
        readonly=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).lst_price)

    list_price3 = fields.Float(
        'Price PVP 3',
        readonly=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).list_price3)

    # list_price4 = fields.Float(
    #     'Price PVP 4',
    #     readonly=True,
    #     default=lambda self:
    #     self.env['product.product'].browse(self.env.context.get('active_id', False)).list_price4)

    pvd1_price = fields.Float(
        'Price PVD 1',
        readonly=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).pvd1_price)

    pvd2_price = fields.Float(
        'Price PVD 2',
        readonly=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).pvd2_price)

    pvd3_price = fields.Float(
        'Price PVD 3',
        readonly=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).pvd3_price)

    # pvd4_price = fields.Float(
    #     'Price PVD 4',
    #     readonly=True,
    #     default=lambda self:
    #     self.env['product.product'].browse(self.env.context.get('active_id', False)).pvd4_price)

    pvi1_price = fields.Float(
        'Price PVI 1',
        readonly=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).pvi1_price)

    pvi2_price = fields.Float(
        'Price PVI 2',
        readonly=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).pvi2_price)

    pvi3_price = fields.Float(
        'Price PVI 3',
        readonly=True,
        default=lambda self:
        self.env['product.product'].browse(self.env.context.get('active_id', False)).pvi3_price)

    # pvi4_price = fields.Float(
    #     'Price PVI 4',
    #     readonly=True,
    #     default=lambda self:
    #     self.env['product.product'].browse(self.env.context.get('active_id', False)).pvi4_price)

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
        ctx = dict(self.env.context)
        ctx['warehouse_id'] = self.warehouse_id.id
        ctx['location'] = self.location_orig_id.id
        product = self.env['product.product']. \
            with_context(ctx).browse(self.product_id.id)
        outlet_id = product.id
        act_prod = False
        create_loss = False
        outlet_product_selected = []

        if self.state == "first":
            res = super(ProductOutletWizard, self).make_move()
        else:
            if product.qty_available < self.qty:
                raise ValidationError(_("Qty to outlet must be <= qty available"))
            if self.qty <= 0:
                raise ValidationError(_("Qty to outlet must be >=0"))
            category_selected = self.env['product.category'].browse(int(self.categ_id))
            outlet_product_selected = self.env['product.product'].search(
                [('default_code', '=', self.product_id.name + category_selected.name)]
            )

            res = super(ProductOutletWizard, self).make_move()

            if self.state == "last":
                act_prod = True
                create_loss = True
                price_outlet = self.list_price - (self.list_price *
                                                  (category_selected.percent / 100))

                price_outlet2 = self.list_price2 - (self.list_price2 *
                                                    (category_selected.percent / 100))

                price_outlet3 = self.list_price3 - (self.list_price3 *
                                                    (category_selected.percent / 100))

                price_outlet4 = self.list_price4 - (self.list_price4 *
                                                    (category_selected.percent / 100))

                price_outlet_pvd = self.pvd1_price - (self.pvd1_price *
                                                      (category_selected.percent / 100))

                price_outlet_pvd2 = self.pvd2_price - (self.pvd2_price *
                                                       (category_selected.percent / 100))

                price_outlet_pvd3 = self.pvd3_price - (self.pvd3_price *
                                                       (category_selected.percent / 100))

                price_outlet_pvd4 = self.pvd4_price - (self.pvd4_price *
                                                       (category_selected.percent / 100))

                price_outlet_pvi = self.pvi1_price - (self.pvi1_price *
                                                      (category_selected.percent / 100))

                price_outlet_pvi2 = self.pvi2_price - (self.pvi2_price *
                                                       (category_selected.percent / 100))

                price_outlet_pvi3 = self.pvi3_price - (self.pvi3_price *
                                                       (category_selected.percent / 100))

                price_outlet_pvi4 = self.pvi4_price - (self.pvi4_price *
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
                    'list_price4': price_outlet4,
                    'commercial_cost': self.commercial_cost,
                    'list_price': price_outlet,
                    'pvd1_price': price_outlet_pvd,
                    'pvd2_price': price_outlet_pvd2,
                    'pvd3_price': price_outlet_pvd3,
                    'pvd4_price': price_outlet_pvd4,
                    'pvi1_price': price_outlet_pvi,
                    'pvi2_price': price_outlet_pvi2,
                    'pvi3_price': price_outlet_pvi3,
                    'pvi4_price': price_outlet_pvi4
                }
                outlet_product.write(values)

        return res
