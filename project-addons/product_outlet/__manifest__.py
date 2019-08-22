# © 2014 Pexego Sistemas Informáticos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Outlet",
    'version': '11.0.1.0.0',
    'category': 'product',
    'license': 'AGPL-3',
    'description': """Manage outlet products.""",
    'author': 'Pexego Sistemas Informáticos',
    'website': 'www.pexego.es',
    "depends": ['base',
                'product',
                'stock',
                'equivalent_products',
                'product_pricelist_custom'],
    "data": ['data/product_data.xml',
             'data/cron.xml',
             'wizard/product_outlet_wizard_view.xml',
             'views/product_category.xml'],
    "installable": True
}
