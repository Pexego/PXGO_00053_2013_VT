# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'UBL EDI exchange from IT odoo',
    'version': '11.0.0.0.1',
    'author': 'Comunitea',
    'webbsite': 'https://www.comunitea.com',
    'description': """""",
    'depends': ['sale_order_import_ubl', 'stock_deposit',
                'crm_claim_rma_custom', 'sale_stock'],
    'category': 'EDI',
    'data': ['data/ubl_edi_from_it_data.xml'],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
