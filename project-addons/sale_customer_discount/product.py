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
import openerp.addons.decimal_precision as dp


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
                'margin_pvi1': 0.0,
                'margin_pvi2': 0.0,
                'margin_pvi3': 0.0
            }
            if product.list_price and product.pvd1_relation:
                res[product.id]['margin_pvd1'] = \
                    1 - (product.standard_price /
                         (product.list_price * product.pvd1_relation))
            if product.list_price2 and product.pvd2_relation:
                res[product.id]['margin_pvd2'] = \
                    1 - (product.standard_price /
                         (product.list_price2 * product.pvd2_relation))
            if product.list_price3 and product.pvd3_relation:
                res[product.id]['margin_pvd3'] = \
                    1 - (product.standard_price /
                         (product.list_price3 * product.pvd3_relation))
            if product.pvi1_price:
                res[product.id]['margin_pvi1'] = \
                    1 - (product.standard_price / product.pvi1_price)
            if product.pvi2_price:
                res[product.id]['margin_pvi2'] = \
                    1 - (product.standard_price / product.pvi2_price)
            if product.pvi3_price:
                res[product.id]['margin_pvi3'] = \
                    1 - (product.standard_price / product.pvi3_price)
        return res

    _columns = {
        'list_price2': fields.float('Sale Price',
                                    digits_compute=dp.get_precision('Product \
                                                                    Price')),
        'list_price3': fields.float('Sale Price 2',
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
        'pvi1_price': fields.float('PVI 1 price', digits_compute =
                                   dp.get_precision('Product Price')),
        'pvi2_price': fields.float('PVI 2 price', digits_compute =
                                   dp.get_precision('Product Price')),
        'pvi3_price': fields.float('PVI 3 price', digits_compute =
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
    }
