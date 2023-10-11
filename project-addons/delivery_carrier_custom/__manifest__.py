{
    'name': 'Delivery Carrier Custom',
    'version': '1.0',
    'category': 'Customization',
    'description': 'Customizes Delivery Carrier',
    'author': 'Visiotech',
    'depends': [
        'delivery_carrier_partner',
        'sale_custom',
        'customer_area'
    ],
    'data': [
        'views/partner_view.xml',
        'views/delivery_carrier.xml',
        'views/country_view.xml',
        'views/sale_view.xml',
        'views/stock_view.xml',
        'wizard/picking_tracking_status_view.xml',
        'data/parameters.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True
}
