# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
                "product_virtual_stock_conservative",
                "purchase_proposal",
                "product_brand",
                "mrp",
                "sale_product_customize",
                "onchange_helper"
                ],
    "data": ["views/minimum_days_view.xml",
             "wizard/add_to_purchase_order_view.xml",
             "views/product_view.xml",
             "views/under_minimum_view.xml",
             "views/stock_warehouse_orderpoint_view.xml",
             "security/ir.model.access.csv",
             "wizard/create_purchase_order_view.xml",
             "wizard/assign_purchase_order_view.xml",
             "wizard/create_production_order_view.xml",
             "wizard/calc_cicle_supplier_product_view.xml",
             "data/product_stock_unsafety_data.xml"],
    "installable": True,
    "application": True,
}
