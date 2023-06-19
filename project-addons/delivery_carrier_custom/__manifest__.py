{
    'name': 'Delivery Carrier Custom',
    'version': '1.0',
    'category': 'Customization',
    'description': 'Customizes Delivery Carrier',
    'author': 'Visiotech',
    'depends': [
        'delivery_carrier_partner',
        'sale_custom'
    ],
    'data': [
        'views/partner_view.xml',
        'views/delivery_carrier.xml',
        'views/country_view.xml',
        'views/sale_view.xml'
    ],
    'installable': True
}
