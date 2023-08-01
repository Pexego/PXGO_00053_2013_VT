{
    'name': 'Papeur connector',
    'version': '1.0',
    'category': 'Extra Tools',
    'description': "",
    'author': 'Visiotech',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/parameters.xml',
        'data/groups.xml',
        'views/picking_views.xml'
    ],
    'installable': True,
    'auto_install': False,
}
