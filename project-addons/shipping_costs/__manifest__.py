{
    'name': 'Shipping costs',
    'version': '1.0',
    'summary': '',
    'description': '',
    'author': 'Visiotech',
    'depends': ['sale', 'transportation', 'base', 'sale_order_board', 'advise_special_shipping_costs'],
    'data': ['security/ir.model.access.csv', 'views/shipping_cost_view.xml'],
    'installable': True,
    'auto_install': False,
}
