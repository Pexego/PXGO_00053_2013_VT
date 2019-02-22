{
    'name': 'Crm Claim phonecall',
    'version': '11.0',
    'category': 'crm',
    'description': """
        Crm claim phonecall:
    """,
    'author': ' ',
    'website': '',
    "depends": ['crm_claim_rma_custom',
                'crm_phonecall',
                'mail'],
    "data": ['wizard/crm_phonecall_view.xml',
             'wizard/email_template.xml'
             ],
    "installable": True
}