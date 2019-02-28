# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Tests management',
    'version': '11.0.1.0.0',
    'category': 'Accounting',
    'author': 'Comunitea',
    'website': 'www.comunitea.com',
    "depends": ['sale', 'account', 'sale_stock', 'stock_account', 'auth_crypt'],
    "data": ['security/test_management_security.xml',
             'wizard/sale_make_invoice_advance.xml',
             'views/sale_view.xml',
             'views/company_view.xml'],
    "installable": True
}
