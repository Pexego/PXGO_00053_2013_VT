{
    'name': "Product battery",
    'version': '11.0',
    'category': 'product',
    'description': """""",
    'author': 'Visiotech',
    'website': 'www.visiotechsecurity.com',
    "depends": ['product', 'stock'],
    "data": ['data/battery_data.xml', 'views/product_view.xml', 'views/battery_view.xml', 'views/sale_view.xml',
             'security/ir.model.access.csv'
             ],
    "installable": True
}
