{
    'name': "National Arrivals ES",
    'version': '11.0',
    'category': 'purchase',
    'description': """
    Creates a menu where can be found incoming pickings in national territory
    """,
    'author': 'Visiotech',
    "depends": [
        'l10n_es',
        'purchase',
        'purchase_picking'
    ],
    "data": [
        'views/stock_view.xml'
    ],
    "installable": True
}
