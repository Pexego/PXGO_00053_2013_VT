##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos
#    $Omar Castiñeira Saavedra <omar@pcomunitea.com>$
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
    'name': "Custom reports links",
    'version': '11.0.1.0.0',
    'category': 'Custom',
    'description': """Customized report links""",
    'author': 'Comunitea',
    'website': 'www.comunitea.com',
    "depends": ['sale', 'purchase', 'account', 'stock_custom',
                'stock_reserve_sale', 'sale_proforma_report',
                'stock_picking_report_valued', 'crm_claim', 'product'],
    "data": [
        "data/report_paperformat.xml",
        "views/custom_layout.xml",
        "views/stock_custom_report.xml",
        "views/report_sale_order.xml",
        "views/report_purchase_order.xml",
        "views/report_stock_picking.xml",
        "views/report_stock_picking_valued.xml",
        "views/report_invoice.xml",
        "views/report_claim.xml",
        "views/report_overdue.xml"],
    "installable": True
}
