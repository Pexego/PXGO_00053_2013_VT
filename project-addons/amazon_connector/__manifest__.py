{
    'name': "Amazon Connector",
    'version': '1.0',
    'category': 'Custom',
    'description': """Added a connector between Amazon and Odoo""",
    'author': 'Visiotech',
    "depends": ['base', 'sale', 'account', 'product', 'stock_deposit','custom_account', 'l10n_es_aeat'],
    'external_dependencies': {
        'python': ['sp_api'],
    },
    "data": ["data/data.xml", "data/email.xml", "data/cron.xml", "security/ir.model.access.csv",
             "report/account_invoice_report_view.xml", "views/company.xml", "views/product.xml",
             "views/amazon_sale_order.xml", "views/amazon_company.xml","views/amazon_marketplace.xml",
             "views/amazon_returns.xml", "views/stock_deposit.xml", "wizard/retry_orders.xml",
             "wizard/create_full_invoices.xml", "views/invoice.xml", "views/amazon_settlement.xml",
             "views/partner_view.xml"
             ],
    "installable": True
}
