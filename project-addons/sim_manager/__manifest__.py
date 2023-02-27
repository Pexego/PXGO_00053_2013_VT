{
    'name': 'SIM cards manager',
    'version': '1.0',
    'summary': '',
    'description': '',
    'author': 'Visiotech',
    'depends': ['mrp', 'barcode_action', 'crm_claim_rma', 'stock_custom', 'flask_middleware_connector', 'mail'],
    'data': ['views/sim_view.xml', 'views/partner_view.xml', 'views/email_template.xml', 'views/sale_view.xml',
             'security/ir.model.access.csv', 'data/parameters.xml', 'data/cron.xml', 'data/email_template.xml'],
    'installable': True,
    'auto_install': False,
}
