{
    'name': 'Dropship Italia IT',
    'version': '1.0',
    'description': 'Process the purchases from dropships ',
    'author': 'Visiotech',
    'depends': [
        'purchase',
        'stock_dropshipping',
        'delivery_carrier_custom',
        'product_battery',
        'stock_custom'
    ],
    'data': [
        'views/sale_view.xml',
        'views/picking_view.xml',
        'views/partner_view.xml',
        'data/email_templates.xml'
    ],
    'installable': True,
    'auto_install': False,
}
