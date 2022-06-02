# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account custom it ',
    'version': '11.0.1.0.0',
    'category': 'account',
    'description': """
        Account customizations:
            -Several little changes on custom_account
    """,
    'author': 'Visiotech',
    'website': '',
    "depends": ['custom_account', 'sale', 'account', 'l10n_it_fiscal_document_type',
                'l10n_it_ricevute_bancarie'],
    "data": ["security/ir.model.access.csv", "wizard/reconcile_riba_with_statement_lines_wzd_view.xml",
             "views/account_view.xml", "views/riba_view.xml"],
    "installable": True
}
