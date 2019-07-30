# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Sale Order Invoice Policy",
    'version': '11.0.',
    'category': 'sale',
    'description': """""",
    'author': 'Visiotech',
    "depends": ['base', 'sale_force_invoiced', 'sale_stock'],
    "data": ['security/sale_security.xml',
             'views/sale_order_view.xml'],
    "installable": True
}
