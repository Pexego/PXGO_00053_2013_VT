{
    'name': 'Outlook Calendar',
    'version': '1.0',
    'category': 'Extra Tools',
    'description': "",
    'author': 'Visiotech',
    'depends': ['calendar'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/parameters.xml',
        'views/res_users_views.xml',
        'views/o_calendar_views.xml',
        'views/calendar_views.xml'
    ],
    'installable': True,
    'auto_install': False,
}
