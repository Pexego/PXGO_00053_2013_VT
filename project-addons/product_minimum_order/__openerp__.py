# -*- coding: utf-8 -*-
{
    "name": "Product Minimum Order",
    "version": "0.1",
    "category": "Sale Order",
    "description": """
This module allow to set a minimun order for a product. Once is chosen in the 
sale order, the system will check the quantity so it has to be at least the minimum
or a multiple.
    """,
    "author": "Ruben Cerrillo",
    "depends": [
        "product",
        "sale",
        "sale_stock"
    ],
    "data": [
        "views/product_view.xml"
    ],
    "installable": True
}