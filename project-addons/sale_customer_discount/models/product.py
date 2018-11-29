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

from openerp.osv import osv, fields
import odoo.addons.decimal_precision as dp

class product_product(osv.osv):
    _inherit = 'product.product'

    def _get_margins(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res = dict.fromkeys(ids, 0.0)
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = {
                'margin_pvd1': 0.0,
                'margin_pvd2': 0.0,
                'margin_pvd3': 0.0,
                'margin_pvd4': 0.0,
                'margin_pvi1': 0.0,
                'margin_pvi2': 0.0,
                'margin_pvi3': 0.0,
                'margin_pvi4': 0.0,
                'margin_pvd_pvi_1': 0.0,
                'margin_pvd_pvi_2': 0.0,
                'margin_pvd_pvi_3': 0.0,
                'margin_pvd_pvi_4': 0.0
            }
            if product.list_price and product.pvd1_relation:
                res[product.id]['margin_pvd1'] = \
                    (1 - (product.standard_price /
                         (product.list_price * product.pvd1_relation))) * 100.0
            if product.list_price2 and product.pvd2_relation:
                res[product.id]['margin_pvd2'] = \
                    (1 - (product.standard_price /
                         (product.list_price2 * product.pvd2_relation))) * \
                    100.0
            if product.list_price3 and product.pvd3_relation:
                res[product.id]['margin_pvd3'] = \
                    (1 - (product.standard_price /
                         (product.list_price3 * product.pvd3_relation))) * \
                    100.0
            if product.list_price4 and product.pvd4_relation:
                res[product.id]['margin_pvd4'] = \
                    (1 - (product.standard_price /
                         (product.list_price4 * product.pvd4_relation))) * \
                    100.0
            if product.pvi1_price:
                res[product.id]['margin_pvi1'] = \
                    (1 - (product.standard_price / product.pvi1_price)) * 100.0
                if product.pvd1_price:
                    res[product.id]['margin_pvd_pvi_1'] = \
                        ((product.pvd1_price - product.pvi1_price) / product.pvd1_price) * 100
            if product.pvi2_price:
                res[product.id]['margin_pvi2'] = \
                    (1 - (product.standard_price / product.pvi2_price)) * 100.0
                if product.pvd2_price:
                    res[product.id]['margin_pvd_pvi_2'] = \
                        ((product.pvd2_price - product.pvi2_price) / product.pvd2_price) * 100
            if product.pvi3_price:
                res[product.id]['margin_pvi3'] = \
                    (1 - (product.standard_price / product.pvi3_price)) * 100.0
                if product.pvd3_price:
                    res[product.id]['margin_pvd_pvi_3'] = \
                        ((product.pvd3_price - product.pvi3_price) / product.pvd3_price) * 100
            if product.pvi4_price:
                res[product.id]['margin_pvi4'] = \
                    (1 - (product.standard_price / product.pvi4_price)) * 100.0
                if product.pvd4_price:
                    res[product.id]['margin_pvd_pvi_4'] = \
                        ((product.pvd4_price - product.pvi4_price) / product.pvd4_price) * 100
        return res

    _columns = {
        'list_price2': fields.float('Sale Price',
                                    digits_compute=dp.get_precision('Product \
                                                                    Price')),
        'list_price3': fields.float('Sale Price 2',
                                    digits_compute=dp.get_precision('Product \
                                                                    Price')),
        'list_price4': fields.float('Sale Price 3',
                                    digits_compute=dp.get_precision('Product \
                                                                    Price')),
        'commercial_cost': fields.float('Commercial Cost',
                                        digits_compute=
                                        dp.get_precision('Product Price')),
        'pvd1_relation': fields.float('PVP/PVD 1 relation', digits=(4, 2),
                                      default=0.5),
        'pvd2_relation': fields.float('PVP 2 / PVD 2 relation', digits=(4, 2),
                                      default=0.5),
        'pvd3_relation': fields.float('PVP 3 / PVD 3 relation', digits=(4, 2),
                                      default=0.5),
        'pvd4_relation': fields.float('PVP 4 / PVD 4 relation', digits=(4, 2),
                                      default=0.5),
        'pvd1_price': fields.float('PVD 1 price', digits_compute=
                                   dp.get_precision('Product Price')),
        'pvd2_price': fields.float('PVD 2 price', digits_compute=
                                   dp.get_precision('Product Price')),
        'pvd3_price': fields.float('PVD 3 price', digits_compute=
                                   dp.get_precision('Product Price')),
        'pvd4_price': fields.float('PVD 4 price', digits_compute=
                                   dp.get_precision('Product Price')),
        'pvi1_price': fields.float('PVI 1 price', digits_compute =
                                   dp.get_precision('Product Price')),
        'pvi2_price': fields.float('PVI 2 price', digits_compute =
                                   dp.get_precision('Product Price')),
        'pvi3_price': fields.float('PVI 3 price', digits_compute =
                                   dp.get_precision('Product Price')),
        'pvi4_price': fields.float('PVI 4 price', digits_compute=
                                   dp.get_precision('Product Price')),
        'margin_pvd1': fields.function(_get_margins,
                                       string="PVD 1 Margin",
                                       type="float", multi="_get_margins",
                                       digits=(5, 2),
                                       store={'product.product':
                                              (lambda self, cr, uid, ids,
                                               c={}: ids,
                                               ['list_price', 'pvd1_relation',
                                                'standard_price'], 10), }),
        'margin_pvd2': fields.function(_get_margins,
                                       string="PVD 2 Margin",
                                       type="float", multi="_get_margins",
                                       digits=(5, 2),
                                       store={'product.product':
                                              (lambda self, cr, uid, ids,
                                               c={}: ids,
                                               ['list_price2', 'pvd2_relation',
                                                'standard_price'], 10), }),
        'margin_pvd3': fields.function(_get_margins,
                                       string="PVD 3 Margin",
                                       type="float", multi="_get_margins",
                                       digits=(5, 2),
                                       store={'product.product':
                                              (lambda self, cr, uid, ids,
                                               c={}: ids,
                                               ['list_price3', 'pvd3_relation',
                                                'standard_price'], 10), }),
        'margin_pvd4': fields.function(_get_margins,
                                       string="PVD 4 Margin",
                                       type="float", multi="_get_margins",
                                       digits=(5, 2),
                                       store={'product.product':
                                                  (lambda self, cr, uid, ids,
                                                          c={}: ids,
                                                   ['list_price4', 'pvd4_relation',
                                                    'standard_price'], 10), }),
        'margin_pvi1': fields.function(_get_margins,
                                       string="PVI 1 Margin",
                                       type="float", multi="_get_margins",
                                       digits=(5, 2),
                                       store={'product.product':
                                              (lambda self, cr, uid, ids,
                                               c={}: ids,
                                               ['pvi1_price',
                                                'standard_price'], 10), }),
        'margin_pvi2': fields.function(_get_margins,
                                       string="PVI 2 Margin",
                                       type="float", multi="_get_margins",
                                       digits=(5, 2),
                                       store={'product.product':
                                              (lambda self, cr, uid, ids,
                                               c={}: ids,
                                               ['pvi2_price',
                                                'standard_price'], 10), }),
        'margin_pvi3': fields.function(_get_margins,
                                       string="PVI 3 Margin",
                                       type="float", multi="_get_margins",
                                       digits=(5, 2),
                                       store={'product.product':
                                              (lambda self, cr, uid, ids,
                                               c={}: ids,
                                               ['pvi3_price',
                                                'standard_price'], 10), }),
        'margin_pvi4': fields.function(_get_margins,
                                       string="PVI 4 Margin",
                                       type="float", multi="_get_margins",
                                       digits=(5, 2),
                                       store={'product.product':
                                                  (lambda self, cr, uid, ids,
                                                          c={}: ids,
                                                   ['pvi4_price',
                                                    'standard_price'], 10), }),
        'margin_pvd_pvi_1': fields.function(_get_margins,
                                       string='PVD/PVI 1 margin',
                                       type="float", multi="_get_margins",
                                       digits=(5, 2),
                                       store={'product.product':
                                              (lambda self, cr, uid, ids,
                                               c={}: ids,
                                               ['pvi1_price',
                                                'pvd1_price'], 10), }),
        'margin_pvd_pvi_2': fields.function(_get_margins,
                                       string='PVD/PVI 2 margin',
                                       type="float", multi="_get_margins",
                                       digits=(5, 2),
                                       store={'product.product':
                                              (lambda self, cr, uid, ids,
                                               c={}: ids,
                                               ['pvi2_price',
                                                'pvd2_price'], 10), }),
        'margin_pvd_pvi_3': fields.function(_get_margins,
                                       string='PVD/PVI 3 margin',
                                       type="float", multi="_get_margins",
                                       digits=(5, 2),
                                       store={'product.product':
                                              (lambda self, cr, uid, ids,
                                               c={}: ids,
                                               ['pvi3_price',
                                                'pvd3_price'], 10), }),
        'margin_pvd_pvi_4': fields.function(_get_margins,
                                            string='PVD/PVI 4 margin',
                                            type="float", multi="_get_margins",
                                            digits=(5, 2),
                                            store={'product.product':
                                                       (lambda self, cr, uid, ids,
                                                               c={}: ids,
                                                        ['pvi4_price',
                                                         'pvd4_price'], 10), }),
    }

    def pvd1_price_change(self, cr, uid, ids, pvd1_price, standard_price, pvi1_price, pvd1_relation=0.5):
        # res = {'value': {'list_price': (1.0 / pvd1_relation) * pvd1_price,
        #                 'margin_pvd1': (1 - (standard_price / pvd1_price)) * 100.0}}
        if pvd1_price:
            list_price = (1.0 / pvd1_relation) * pvd1_price
            margin_pvd = (1 - (standard_price / pvd1_price)) * 100.0
            margin_pvd_pvi_1 = ((pvd1_price - pvi1_price) / pvd1_price) * 100
        else:
            list_price = 0
            margin_pvd = 0
            margin_pvd_pvi_1 = 0

        res = {'value': {'lst_price': list_price,
                         'margin_pvd1': margin_pvd,
                         'margin_pvd_pvi_1': margin_pvd_pvi_1}}
        return res

    def pvd2_price_change(self, cr, uid, ids, pvd2_price, standard_price, pvi2_price, pvd2_relation=0.5):
        if pvd2_price:
            list_price = (1.0 / pvd2_relation) * pvd2_price
            margin_pvd = (1 - (standard_price / pvd2_price)) * 100.0
            margin_pvd_pvi_2 = ((pvd2_price - pvi2_price) / pvd2_price) * 100
        else:
            list_price = 0
            margin_pvd = 0
            margin_pvd_pvi_2 = 0

        res = {'value': {'list_price2': list_price,
                         'margin_pvd2': margin_pvd,
                         'margin_pvd_pvi_2': margin_pvd_pvi_2}}
        return res

    def pvd3_price_change(self, cr, uid, ids, pvd3_price, standard_price, pvi3_price, pvd3_relation=0.5):
        if pvd3_price:
            list_price = (1.0 / pvd3_relation) * pvd3_price
            margin_pvd = (1 - (standard_price / pvd3_price)) * 100.0
            margin_pvd_pvi_3 = ((pvd3_price - pvi3_price) / pvd3_price) * 100
        else:
            list_price = 0
            margin_pvd = 0
            margin_pvd_pvi_3 = 0

        res = {'value': {'list_price3': list_price,
                         'margin_pvd3': margin_pvd,
                         'margin_pvd_pvi_3': margin_pvd_pvi_3}}
        return res

    def pvd4_price_change(self, cr, uid, ids, pvd4_price, standard_price, pvi4_price, pvd4_relation=0.5):
        if pvd4_price:
            list_price = (1.0 / pvd4_relation) * pvd4_price
            margin_pvd = (1 - (standard_price / pvd4_price)) * 100.0
            margin_pvd_pvi_4 = ((pvd4_price - pvi4_price) / pvd4_price) * 100
        else:
            list_price = 0
            margin_pvd = 0
            margin_pvd_pvi_4 = 0

        res = {'value': {'list_price4': list_price,
                         'margin_pvd4': margin_pvd,
                         'margin_pvd_pvi_4': margin_pvd_pvi_4}}
        return res

    def pvi1_price_change(self, cr, uid, ids, standard_price, pvi1_price, pvd1_price):
        # res = {'value': {'margin_pvi1': (1 - (standard_price / pvi1_price)) * 100.0}}
        if pvd1_price:
            margin_pvd_pvi_1 = ((pvd1_price - pvi1_price) / pvd1_price) * 100
        else:
            margin_pvd_pvi_1 = 0

        if pvi1_price:
            margin_pvi1 = (1 - (standard_price / pvi1_price)) * 100.0
        else:
            margin_pvi1 = 0

        res = {'value': {'margin_pvi1': margin_pvi1,
                         'margin_pvd_pvi_1': margin_pvd_pvi_1}}

        return res

    def pvi2_price_change(self, cr, uid, ids, standard_price, pvi2_price, pvd2_price):
        if pvd2_price:
            margin_pvd_pvi_2 = ((pvd2_price - pvi2_price) / pvd2_price) * 100
        else:
            margin_pvd_pvi_2 = 0

        if pvi2_price:
            margin_pvi2 = (1 - (standard_price / pvi2_price)) * 100.0
        else:
            margin_pvi2 = 0

        res = {'value': {'margin_pvi2': margin_pvi2,
                         'margin_pvd_pvi_2': margin_pvd_pvi_2}}

        return res

    def pvi3_price_change(self, cr, uid, ids, standard_price, pvi3_price, pvd3_price):
        if pvd3_price:
            margin_pvd_pvi_3 = ((pvd3_price - pvi3_price) / pvd3_price) * 100
        else:
            margin_pvd_pvi_3 = 0

        if pvi3_price:
            margin_pvi3 = (1 - (standard_price / pvi3_price)) * 100.0
        else:
            margin_pvi3 = 0

        res = {'value': {'margin_pvi3': margin_pvi3,
                         'margin_pvd_pvi_3': margin_pvd_pvi_3}}

        return res

    def pvi4_price_change(self, cr, uid, ids, standard_price, pvi4_price, pvd4_price):
        if pvd4_price:
            margin_pvd_pvi_4 = ((pvd4_price - pvi4_price) / pvd4_price) * 100
        else:
            margin_pvd_pvi_4 = 0

        if pvi4_price:
            margin_pvi4 = (1 - (standard_price / pvi4_price)) * 100.0
        else:
            margin_pvi4 = 0

        res = {'value': {'margin_pvi4': margin_pvi4,
                         'margin_pvd_pvi_4': margin_pvd_pvi_4}}

        return res

