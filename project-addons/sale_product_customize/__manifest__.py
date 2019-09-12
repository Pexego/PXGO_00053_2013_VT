# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Sale customizations",
    'version': '11.0.1.0.0',
    'category': 'sale',
    'description': """""",
    'author': 'Pexego',
    'website': 'www.pexego.es',
    "depends": ['base', 'sale', 'stock', 'sale_stock', 'mrp', 'product',
                'stock_reserve_sale', 'purchase',
                'sale_customer_discount', 'product_states'],
    "data": ['view/sale_view.xml', 'view/product_view.xml',
             'view/stock_reserve_view.xml', 'view/mrp_production_view.xml',
             'view/mrp_customize.xml',
             'data/customize_type_data.xml',
             'wizard/mrp_customization_view.xml',
             'wizard/mrp_product_produce_view.xml',
             'security/ir.model.access.csv'
             ],
    "installable": True
}
