{
    'name': 'Dropship Italia',
    'version': '1.0',
    'description': 'Allow the creation of the dropship contacts where an order come from Italy',
    'author': 'Visiotech',
    'depends': ['stock', 'delivery_carrier_custom','stock_custom'],
    'data': [
        'views/partner_view.xml',
        'views/delivery_carrier_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
