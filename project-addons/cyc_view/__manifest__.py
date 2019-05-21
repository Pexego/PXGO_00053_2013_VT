# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'CyC report',
    'version': '11.0.1.0.0',
    'category': '',
    'description': "Shows the invoices grouped by country and year for "
                   "export",
    'author': 'Comunitea',
    'website': '',
    "depends": ['account', 'account_payment_partner', 'customer_area',
                'account_credit_control', 'partner_risk_insurance'],
    "data": ['views/account_invoice_cyc_view.xml',
             'security/ir.model.access.csv',
             'views/account_view.xml'],
    "installable": True
}
