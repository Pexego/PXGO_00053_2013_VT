
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

{
    "name": "Promotions Extend",
    "version": "1.0",
    "author": "Pexego",
    'website': 'www.pexego.es',
    "category": "Generic Modules/Sales & Purchases",
    "description": """
Promotions extend
========================================
Features:
1. Lets you apply discounts by product tags.
""",
    "depends": ["base",
                "openerp_sale_promotions",
                "equivalent_products",
                "stock_reserve_sale",
                "product_brand",
                "sale_product_customize"],
    "data": [
        "sale_view.xml",
        "rule.xml",
        "product_view.xml"

    ],
    "demo": [],
    'auto_install': False,
    "installable": True,
    'images': [],
}
