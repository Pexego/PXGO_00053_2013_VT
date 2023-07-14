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
                'product_harmonized_system',
                'purchase',
                'intrastat_product',
                'purchase_picking'],
    "data": ['data/product.xml',
             'views/stock_view.xml',
             'views/import_sheet_view.xml',
             'views/stock_landed_costs_view.xml',
             'views/product_view.xml',
             'views/hs_code_view.xml',
             'security/ir.model.access.csv'],
    "installable": True
}
