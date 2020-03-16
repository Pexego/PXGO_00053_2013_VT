{
    'name': "PEC automatico",
    'version': '1.0',
    'category': 'Invoice',
    'description': """This module automatizes the invoice sending to PEC""",
    'author': 'Visiotech',
    'website': '',
    "depends": ['l10n_it_fatturapa', 'l10n_it_fatturapa_out'],
    "data": ["views/invoice_view.xml", "views/company_view.xml"],
    "installable": True
}
