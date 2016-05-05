# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos
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
{
    "name": "Product under minimums",
    "version": "8.0.0.1.0",
    "author": "Comunitea",
    "category": "Purchases",
    "website": "www.comunitea.com",
    "description": """
PRODUCT UNDER MINIMUMS
=====================================================

Module that adds the management to the products under minimal.

    """,
    "images": [],
    "depends": ["base",
                "product",
                "sale",
                "purchase",
                "stock",
                "procurement",
                "product_virtual_stock_conservative",
                "purchase_proposal"
                ],
    "data": ["minimum_days_view.xml",
             "product_view.xml",
             "under_minimum_view.xml",
             "stock_warehouse_orderpoint_view.xml",
             "stock_view.xml",
             "security/ir.model.access.csv"],
    "installable": True,
    "application": True,
}
