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
    "depends": ['custom_account','account','l10n_it_fiscal_document_type'],
    "data": ["security/ir.model.access.csv"],
    "installable": True
}
