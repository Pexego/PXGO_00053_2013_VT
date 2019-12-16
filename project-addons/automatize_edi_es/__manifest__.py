# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Automatize edi's workflow in ES",
    'version': '11.0.0.0.1',
    'author': 'Comunitea',
    'webbsite': 'https://www.comunitea.com',
    'description': """""",
    'depends': ['ubl_edi_from_it', 'ubl_edi_to_it', 'base_io_folder',
                'sale_order_import_ubl', 'sale_order_ubl'],
    'category': 'EDI',
    'data': ['report/stock_italy.xml'],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
