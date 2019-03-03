# -*- coding: utf-8 -*-
{
    "name": "Discontinued Product",
    "version": "1.0",
    "category": "Products",
    "description": """
This module allow to mark as discontinued any product,
as long as some conditions will be fulfilled. At the same time
the button commission_free will disappear of the view
    """,
    "author": "David Mora",
    "depends": [
        "product",
        "sale",
        "sale_customer_discount"
    ],
    "data": [
        "views/product_discontinued_view.xml"
    ],
    "installable": True
}
