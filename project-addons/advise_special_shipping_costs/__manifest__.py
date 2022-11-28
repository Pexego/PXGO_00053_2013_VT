{
    "name": "Advise Special Shipping Costs",
    "description": "This module allows you to show an advise on sale orders if the product has the check of special shipping costs marked",
    "version": "0.1",
    "data": [
        "data/data.xml",
        "views/product_view.xml",
        "views/sale_view.xml",
        "views/assets.xml"
    ],
    "depends": ['product','sale','stock','transportation', 'sale_order_board'],
    "installable": True,
}
