{
    'name': "Amazon Connector",
    'version': '1.0',
    'category': 'Custom',
    'description': """Added a connector between Amazon and Odoo""",
    'author': 'Visiotech',
    "depends": ['base', 'sale', 'account', 'product', 'stock_deposit'],
    "data": ["data/data.xml", "views/company.xml", "views/product.xml", "views/amazon_sale_order.xml", "data/cron.xml",
             "data/email.xml",
             "wizard/retry_orders.xml"],
    "installable": True
}
