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
        "transportation",
        "custom_account",
        "sale_customer_discount"
    ],
    "data": [
        "data/user_data.xml",
        "views/product_discontinued_view.xml",
        "data/cron.xml",
        "views/email_template.xml",
        "security/product_discontinued.xml",
        'wizard/discontinue_products_view.xml'
    ],
    "installable": True
}
