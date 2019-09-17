# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Import/Export folders",
    'version': '11.0.0.0.1',
    'author': 'Comunitea',
    'webbsite': 'https://www.comunitea.com',
    'description': """""",
    'depends': ['queue_job'],
    'category': 'EDI',
    'data': ['data/base_io_folder_data.xml',
             'security/ir.model.access.csv',
             'views/base_io_folder_view.xml'],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
