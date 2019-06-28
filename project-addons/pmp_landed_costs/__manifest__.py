# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Stock landed costs by tariff",
    'version': '11.0.0.0.1',
    'category': 'stock',
    'description': """""",
    'author': 'Comunitea Servicios Tecnológicos S.L.',
    'website': 'www.comunitea.com',
    "depends": ['stock_landed_costs',
                'stock_account',
                'transportation'],
    "data": ['views/stock_landed_costs_view.xml',
             'views/product_view.xml'],
    "installable": True
}
