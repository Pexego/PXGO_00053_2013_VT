{
    "name": "custom emails company",
    "version": "1.0",
    "category": "company",
    "description": """
This module was created to allocate new fields in res_company model.
Specifically, translated fields which will be used in the templates send 
to the customers.
    """,
    "author": "David Mora",
    "depends": [
        'base', 'portal', 'custom_report_link'
    ],
    "data": [
        'data/email_albaran.xml',
        'data/email_deposit.xml',
        'data/email_invoice.xml',
        'data/email_Payment_Order_advise_partners.xml',
        'data/email_sale.xml',
        'views/company_fields_custom_view.xml',
        'data/mail_layout_custom.xml',
        'data/mail_layout_invoice.xml',
        'data/mail_layout_sale.xml',
    ],
    "installable": True
}
