{
    'name': "Product Customer Reference",
    'version': '1.0',
    'category': 'sale',
    'description': """Add customer references to products""",
    'author': 'Visiotech',
    'website': '',
    "depends": ['base',
                'sale'],
    "data": ['data/area_data.xml',
              'views/partner.xml',
              'security/ir.model.access.csv'],
    "installable": True
}
