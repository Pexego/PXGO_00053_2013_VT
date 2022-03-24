{
    'name': "Product Customer Reference",
    'version': '1.0',
    'category': 'sale',
    'description': """Add customer references to products""",
    'author': 'Visiotech',
    'website': '',
    "depends": ['base',
                'sale',
                'custom_account'],
    "data": ['data/area_data.xml',
             'data/parameters.xml',
             'views/partner.xml',
             'views/sale_view.xml',
             'security/ir.model.access.csv'],
    "installable": True
}
