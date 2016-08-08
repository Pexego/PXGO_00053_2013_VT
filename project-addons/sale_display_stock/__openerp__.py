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
    "name": "Sale display stock",
    "version": "1.0",
    "author": "Pexego",
    'website': 'www.pexego.es',
    "category": "Sales",
    "description": """
Sales display stock
========================================

    * Displays the real stock of product at each sale order line.
""",
    "depends": ["base", "sale", "stock", "account",
                "product_virtual_stock_conservative"],
    "data": [
        "sale_view.xml",
        "product_view.xml",
        "report/sale_order_line_report.xml",
        "security/ir.model.access.csv",
        "security/sale_display_stock_security.xml"
    ],
    "demo": [],
    'auto_install': False,
    "installable": True,
    'images': [],
}
