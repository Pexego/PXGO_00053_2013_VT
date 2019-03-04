# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Purchase proposal",
    'version': '11.0.1.0.0',
    'category': 'purchase',
    'description': """""",
    'author': 'Pexego Sistemas Informáticos',
    'website': 'www.pexego.es',
    "depends": ['base', 'sale', 'stock', 'sale_stock', 'stock_account',
                'sale_margin_percentage',
                'purchase_last_price_info',
                'sale_customer_discount', 'mrp'],
    "data": ['views/product_view.xml', 'data/ir.cron.xml',
             'security/ir.model.access.csv'],
    "installable": True
}
