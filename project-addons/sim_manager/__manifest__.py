{
    'name': 'SIM cards manager',
    'version': '1.0',
    'summary': '',
    'description': '',
    'author': 'Visiotech',
    'depends': ['mrp', 'barcode_action', 'crm_claim_rma', 'stock_custom'],
    'data': ['views/sim_view.xml', 'views/partner_view.xml', 'views/email_template.xml',
             'security/ir.model.access.csv', 'data/parameters.xml', 'data/cron.xml'],
    'installable': True,
    'auto_install': False,
}
