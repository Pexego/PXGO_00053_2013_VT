# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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

{
    'name': "Sale customizations",
    'version': '1.0',
    'category': 'sale',
    'description': """""",
    'author': 'Pexego',
    'website': 'www.pexego.es',
    "depends": ['base', 'sale', 'stock', 'sale_stock', 'mrp', 'product',
                'stock_reserve_sale', 'sale_commission', 'purchase',
                #TODO: Migrar'hide_product_variants',
                'sale_customer_discount'],
    "data": ['view/sale_view.xml', 'view/product_view.xml',
             'view/stock_reserve_view.xml', 'view/mrp_production_view.xml',
             'view/mrp_customize.xml',
             'data/customize_type_data.xml',
             'wizard/mrp_customization_view.xml',
             'security/ir.model.access.csv'
            ],
    "installable": True
}
