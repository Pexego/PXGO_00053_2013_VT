{
    'name': "Separate purchase orders",
    'version': '11.0',
    'category': 'purchase',
    'description': """This module allows separate purchase orders in other smaller orders""",
    'author': 'Visiotech',
    'website': 'www.visiotechsecurity.es',
    "depends": ['purchase',
                'stock',
                'account'],
    "data": ['wizard/separate_orders_wizard.xml',
             'views/purchase_view.xml'
             ],
    "installable": True
}
