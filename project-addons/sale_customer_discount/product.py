# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
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
import openerp
from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp

class product_product(osv.osv):
    _inherit = 'product.product'

    def _get_margins(self, cr, uid, ids, name, arg, context=None):
        res = {}
        res = dict.fromkeys(ids, 0.0)
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = {
                'cmargin_price2': 0.0,
                'smargin_price2': 0.0,
                'cmargin_price3': 0.0,
                'smargin_price3': 0.0
            }
            cmargin2 =  product.list_price2 - product.commercial_cost
            smargin2 = product.list_price2 - product.standard_price
            cmargin3 = product.list_price3 - product.commercial_cost
            smargin3 = product.list_price3 - product.standard_price
            res[product.id]['cmargin_price2'] = (cmargin2 * 100.0) / product.list_price2
            res[product.id]['smargin_price2'] = (smargin2 * 100.0) / product.list_price2
            res[product.id]['cmargin_price3'] = (cmargin3 * 100.0) / product.list_price3
            res[product.id]['smargin_price3'] = (smargin3 * 100.0) / product.list_price3
            
        return res
    
    _columns = {
        'list_price2': fields.float('Sale Price', digits_compute=dp.get_precision('Product Price'), help="Base price to compute the customer price. Sometimes called the catalog price."),
        'list_price3': fields.float('Sale Price 2', digits_compute=dp.get_precision('Product Price'), help="Base price 2 to compute the customer price. Sometimes called the catalog price."),
        'commercial_cost': fields.float('Commercial Cost', digits_compute=dp.get_precision('Product Price')),
        'cmargin_price2': fields.function(_get_margins,
            string="% Commercial margin", type="float", multi="_get_margins",
            digits_compute=dp.get_precision('Product Price'), 
            store={
                'product.product': (lambda self, cr, uid, ids, c={}: ids, ['list_price2','commercial_cost'], 10),
            }),
        'smargin_price2': fields.function(_get_margins,
            string="% Cost margin", type="float", multi="_get_margins",
            digits_compute=dp.get_precision('Product Price'),
            store={
                'product.product': (lambda self, cr, uid, ids, c={}: ids, ['list_price2','standard_price'], 10),
            }),
        'cmargin_price3': fields.function(_get_margins,
            string="% Commercial margin", type="float", multi="_get_margins",
            digits_compute=dp.get_precision('Product Price'),
            store={
                'product.product': (lambda self, cr, uid, ids, c={}: ids, ['list_price3','commercial_cost'], 10),
            }),
        'smargin_price3': fields.function(_get_margins,
            string="% Cost margin", type="float", multi="_get_margins",
            digits_compute=dp.get_precision('Product Price'),
            store={
                'product.product': (lambda self, cr, uid, ids, c={}: ids, ['list_price3','standard_price'], 10),
            }),
    }
    
