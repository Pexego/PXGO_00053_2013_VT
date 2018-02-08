# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Crm Claim custom',
    'version': '1.0',
    'category': 'crm',
    'description': """
        Crm claim customizations:
    """,
    'author': 'Comunitea',
    'website': '',
    "depends": ['crm_claim_rma','account','account_refund_original',"product_virtual_stock_conservative",
                'sale_display_stock', 'crm_rma_advance_location',
                'custom_partner', 'block_invoices', 'product_pack', 'product_brand'],
    "data": ['crm_claim_view.xml', 'mrp_repair_wkf.xml',
             'data/substate_data.xml', 'security/ir.model.access.csv',
             'wizard/claim_make_picking_view.xml', 'stock_view.xml',
             'wizard/equivalent_products_wizard_view.xml',
             'wizard/claim_make_picking_from_picking_view.xml',
             'wizard/crm_phonecall_view.xml',
             'report/crm_claim_report_view.xml',
             'data/stage_data.xml'],
    "installable": True
}
