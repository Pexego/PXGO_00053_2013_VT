
{
    'name': 'Update follow-up data in account move lines',
    'version': '1.0',
    'license': 'AGPL-3',
    'author': 'Nadia Ferreyra',
    'category': 'Account',
    'depends': ['account',
                'account_credit_control',
                'cyc_view',
                'custom_account'],
    'data': ['data/ir_cron.xml',
             'data/credit_control_data.xml',
             'views/credit_control_communication_view.xml',
             'views/partner_view.xml',
             'wizard/wiz_send_followup_partner_view.xml'],
    'description': '''Update follow-up data in account move lines''',
    'installable': True,
}
