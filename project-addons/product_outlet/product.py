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

from openerp import fields, models, api


class product_product(models.Model):

    _inherit = 'product.product'

    is_outlet = fields.Boolean('Is outlet', compute='_is_outlet')
    normal_product_id = fields.Many2one('product.product', 'normal product')
    outlet_product_ids = fields.One2many('product.product',
                                         'normal_product_id',
                                         'Outlet products')

    @api.one
    def _is_outlet(self):
        outlet_cat = self.env.ref('product_outlet.product_category_outlet')
        if self.categ_id == outlet_cat or \
                self.categ_id.parent_id == outlet_cat:
            self.is_outlet = True
        else:
            self.is_outlet = False

    @api.model
    def cron_update_outlet_price(self):
        outlet_categ_ids = []
        outlet_categ_ids.append(self.env.ref('product_outlet.product_category_o1').id)
        outlet_categ_ids.append(self.env.ref('product_outlet.product_category_o2').id)
        outlet_products = self.env['product.product'].search([('categ_id', 'in', outlet_categ_ids),
                                                              ('normal_product_id.list_price', '!=', 0)],
                                                             order="id desc")
        for product_o in outlet_products:
            origin_product = product_o.normal_product_id
            price_outlet = origin_product.list_price * (1 - product_o.categ_id.percent / 100)
            price_outlet2 = origin_product.list_price2 * (1 - product_o.categ_id.percent / 100)
            price_outlet3 = origin_product.list_price3 * (1 - product_o.categ_id.percent / 100)
            price_outlet4 = origin_product.list_price4 * (1 - product_o.categ_id.percent / 100)
            price_outlet_pvd = origin_product.pvd1_price * (1 - product_o.categ_id.percent / 100)
            price_outlet_pvd2 = origin_product.pvd2_price * (1 - product_o.categ_id.percent / 100)
            price_outlet_pvd3 = origin_product.pvd3_price * (1 - product_o.categ_id.percent / 100)
            price_outlet_pvd4 = origin_product.pvd4_price * (1 - product_o.categ_id.percent / 100)
            price_outlet_pvi = origin_product.pvi1_price * (1 - product_o.categ_id.percent / 100)
            price_outlet_pvi2 = origin_product.pvi2_price * (1 - product_o.categ_id.percent / 100)
            price_outlet_pvi3 = origin_product.pvi3_price * (1 - product_o.categ_id.percent / 100)
            price_outlet_pvi4 = origin_product.pvi4_price * (1 - product_o.categ_id.percent / 100)

            if round(product_o.list_price, 2) != round(price_outlet, 2) or \
                    round(product_o.list_price2, 2) != round(price_outlet2, 2) or \
                    round(product_o.list_price3, 2) != round(price_outlet3, 2) or \
                    round(product_o.list_price4, 2) != round(price_outlet4, 2) or \
                    round(product_o.pvd1_price, 2) != round(price_outlet_pvd, 2) or \
                    round(product_o.pvd2_price, 2) != round(price_outlet_pvd2, 2) or \
                    round(product_o.pvd3_price, 2) != round(price_outlet_pvd3, 2) or \
                    round(product_o.pvd4_price, 2) != round(price_outlet_pvd4, 2) or \
                    round(product_o.pvi1_price, 2) != round(price_outlet_pvi, 2) or \
                    round(product_o.pvi2_price, 2) != round(price_outlet_pvi2, 2) or \
                    round(product_o.pvi3_price, 2) != round(price_outlet_pvi3, 2) or \
                    round(product_o.pvi4_price, 2) != round(price_outlet_pvi4, 2) or \
                    round(product_o.commercial_cost, 2) != round(origin_product.commercial_cost, 2):
                # update all prices
                values = {
                    'standard_price': price_outlet,
                    'list_price': price_outlet,
                    'list_price2': price_outlet2,
                    'list_price3': price_outlet3,
                    'list_price4': price_outlet4,
                    'pvd1_price': price_outlet_pvd,
                    'pvd2_price': price_outlet_pvd2,
                    'pvd3_price': price_outlet_pvd3,
                    'pvd4_price': price_outlet_pvd4,
                    'pvi1_price': price_outlet_pvi,
                    'pvi2_price': price_outlet_pvi2,
                    'pvi3_price': price_outlet_pvi3,
                    'pvi4_price': price_outlet_pvi4,
                    'commercial_cost': origin_product.commercial_cost,
                }
                product_o.write(values)

