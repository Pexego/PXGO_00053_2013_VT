{
    'name': 'Captio Connector',
    'version': '1.0',
    'description': 'Connector for the expenses with the Captio platform',
    'category': '',
    'author': 'Visiotech',
    'depends': ['hr_expense'],
    'data': ['views/res_config_settings_views.xml',
             'views/res_users_view.xml',
             'data/cron.xml',
             'data/parameters.xml',
             'views/account_views.xml'],
    'installable': True,
}
