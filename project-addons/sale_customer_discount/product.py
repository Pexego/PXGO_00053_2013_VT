# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos S.L.
#    $Omar Castiñeira Saavedra$ <omar@comunitea.com>
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

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class product_product(models.Model):
    _inherit = 'product.product'

    @api.depends('list_price', 'pvd1_relation', 'pvd2_relation',
                 'pvd3_relation', 'pvd4_relation', 'standard_price',
                 'pvi1_price', 'pvi2_price', 'pvi3_price', 'pvi4_price')
    def _get_margins(self):
        for product in self:
            if product.list_price and product.pvd1_relation:
                product.margin_pvd1 = \
                    (1 - (product.standard_price /
                         (product.list_price * product.pvd1_relation))) * 100.0
            if product.list_price2 and product.pvd2_relation:
                product.margin_pvd2 = \
                    (1 - (product.standard_price /
                         (product.list_price2 * product.pvd2_relation))) * \
                    100.0
            if product.list_price3 and product.pvd3_relation:
                product.margin_pvd3 = \
                    (1 - (product.standard_price /
                         (product.list_price3 * product.pvd3_relation))) * \
                    100.0
            if product.list_price4 and product.pvd4_relation:
                product.margin_pvd4 = \
                    (1 - (product.standard_price /
                         (product.list_price4 * product.pvd4_relation))) * \
                    100.0
            if product.pvi1_price:
                product.margin_pvi1 = \
                    (1 - (product.standard_price / product.pvi1_price)) * 100.0
                if product.pvd1_price:
                    product.margin_pvd_pvi_1 = \
                        ((product.pvd1_price - product.pvi1_price) / product.pvd1_price) * 100
            if product.pvi2_price:
                product.margin_pvi2 = \
                    (1 - (product.standard_price / product.pvi2_price)) * 100.0
                if product.pvd2_price:
                    product.margin_pvd_pvi_2 = \
                        ((product.pvd2_price - product.pvi2_price) / product.pvd2_price) * 100
            if product.pvi3_price:
                product.margin_pvi3 = \
                    (1 - (product.standard_price / product.pvi3_price)) * 100.0
                if product.pvd3_price:
                    product.margin_pvd_pvi_3 = \
                        ((product.pvd3_price - product.pvi3_price) / product.pvd3_price) * 100
            if product.pvi4_price:
                product.margin_pvi4 = \
                    (1 - (product.standard_price / product.pvi4_price)) * 100.0
                if product.pvd4_price:
                    product.margin_pvd_pvi_4 = \
                        ((product.pvd4_price - product.pvi4_price) / product.pvd4_price) * 100

    list_price2 = fields.Float('Sale Price',
                               digits=dp.get_precision('Product Price'))
    list_price3 = fields.Float('Sale Price 2',
                               digits=dp.get_precision('Product Price'))
    list_price4 = fields.Float('Sale Price 3',
                               digits=dp.get_precision('Product Price'))
    commercial_cost = fields.Float('Commercial Cost',
                                   digits=dp.get_precision('Product Price'))
    pvd1_relation = fields.Float('PVP/PVD 1 relation', digits=(4, 2),
                                 default=0.5)
    pvd2_relation = fields.Float('PVP 2 / PVD 2 relation', digits=(4, 2),
                                 default=0.5)
    pvd3_relation = fields.Float('PVP 3 / PVD 3 relation', digits=(4, 2),
                                 default=0.5)
    pvd4_relation = fields.Float('PVP 4 / PVD 4 relation', digits=(4, 2),
                                 default=0.5)
    pvd1_price = fields.Float('PVD 1 price', digits=
                              dp.get_precision('Product Price'))
    pvd2_price = fields.Float('PVD 2 price', digits=
                              dp.get_precision('Product Price'))
    pvd3_price = fields.Float('PVD 3 price', digits=
                              dp.get_precision('Product Price'))
    pvd4_price = fields.Float('PVD 4 price', digits=
                              dp.get_precision('Product Price'))
    pvi1_price = fields.Float('PVI 1 price', digits =
                              dp.get_precision('Product Price'))
    pvi2_price = fields.Float('PVI 2 price', digits =
                              dp.get_precision('Product Price'))
    pvi3_price = fields.Float('PVI 3 price', digits =
                              dp.get_precision('Product Price'))
    pvi4_price = fields.Float('PVI 4 price', digits=
                              dp.get_precision('Product Price'))
    margin_pvd1 = fields.Float(compute="_get_margins",
                               string="PVD 1 Margin", digits=(5, 2),
                               store=True)
    margin_pvd2 = fields.Float(compute="_get_margins",
                               string="PVD 2 Margin", digits=(5, 2),
                               store=True)
    margin_pvd3 = fields.Float(compute="_get_margins",
                               string="PVD 3 Margin", digits=(5, 2),
                               store=True)
    margin_pvd4 = fields.Float(compute="_get_margins",
                               string="PVD 4 Margin", digits=(5, 2),
                               store=True)
    margin_pvi1 = fields.Float(compute="_get_margins",
                               string="PVI 1 Margin", digits=(5, 2),
                               store=True)
    margin_pvi2 = fields.Float(compute="_get_margins",
                               string="PVI 2 Margin", digits=(5, 2),
                               store=True)
    margin_pvi3 = fields.Float(compute="_get_margins",
                               string="PVI 3 Margin", digits=(5, 2),
                               store=True)
    margin_pvi4 = fields.Float(compute="_get_margins",
                               string="PVI 4 Margin", digits=(5, 2),
                               store=True)
    margin_pvd_pvi_1 = fields.Float(compute="_get_margins",
                                    string='PVD/PVI 1 margin', digits=(5, 2),
                                    store=True)
    margin_pvd_pvi_2 = fields.Float(compute="_get_margins",
                                    string='PVD/PVI 2 margin', digits=(5, 2),
                                    store=True)
    margin_pvd_pvi_3 = fields.Float(compute="_get_margins",
                                    string='PVD/PVI 3 margin', digits=(5, 2),
                                    store=True)
    margin_pvd_pvi_4 = fields.Float(compute="_get_margins",
                                    string='PVD/PVI 4 margin', digits=(5, 2),
                                    store=True)
