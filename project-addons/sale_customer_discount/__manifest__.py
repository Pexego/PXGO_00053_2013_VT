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
    "name": "Sale customer discount",
    "version": "1.0",
    "author": "Pexego",
    'website': 'www.pexego.es',
    "category": "Sales",
    "description": """
Sales customer discount
========================================

    * Add the fields 'sale price 2' and 'commercial cost' to products.
    * Also, added the 'cost margin' and 'commercial margin' of the sale price
    and 'cost margin' and 'commercial margin' of the sale price 2.
""",
    "depends": ["base", "product", "stock_account", "pmp_landed_costs",
                #TODO: Migrar"web_readonly_bypass", "hide_product_variants",
                "purchase"],
    "data": [
        "views/product_view.xml",
    ],
    "demo": [],
    'auto_install': False,
    "installable": True,
    'images': [],
}
