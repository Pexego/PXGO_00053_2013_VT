# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'reserve without save sale custom it',
    'version': '11.0.1.0.0',
    'summary': 'Reserves stock for sales before save it. Add a little customizations for Odoo IT.',
    'category': 'Sales',
    'author': 'Visiotech',
    'license': 'AGPL-3',
    'depends': ['web','stock_dropshipping','reserve_without_save_sale','stock_reserve_sale'],
    'data': ['views/sale.xml'],
    'installable': True,
}
