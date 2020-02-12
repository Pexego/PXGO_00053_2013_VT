# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Automatize edi's workflow in IT",
    'version': '11.0.0.0.1',
    'author': 'Comunitea',
    'webbsite': 'https://www.comunitea.com',
    'description': """""",
    'depends': ['ubl_edi_to_es', 'purchase_order_import_ubl', 'base_io_folder',
                'account_invoice_import_ubl', 'stock_mts_mto_rule',
                'custom_account'],
    'category': 'EDI',
    'data': ['data/automatize_edi_it_data.xml',
             'views/stock_picking_type_view.xml'],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
