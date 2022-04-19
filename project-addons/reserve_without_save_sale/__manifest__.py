# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'reserve without save sale',
    'version': '11.0.1.0.0',
    'summary': 'Reserves stock for sales before save it',
    'category': 'Sales',
    'author': 'Pexego',
    'maintainer': 'Comunitea',
    'website': 'www.comunitea.com',
    'license': 'AGPL-3',
    'depends': ['base', 'web', 'sale',
                'stock_reserve', 'stock_reserve_sale',
                'sale_display_stock', 'order_invoice_policy'
                ], # TODO: sale_product_customize
    'data': ['views/sale.xml', 'views/stock_reserve.xml',
             'data/cron.xml', 'data/parameters.xml', 'data/mail_template.xml', 'security/groups.xml'],
    'installable': True,
}
