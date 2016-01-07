# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saaevdra <omar@comunitea.com>$
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
    "name": "Sale Advance Payment",
    "version": "1.0",
    "author": "Comunitea",
    'website': 'www.counitea.com',
    "category": "Sales",
    "description": """Allow to add advance payments on sales and then use its
 on invoices""",
    "depends": ["base", "sale", "account_voucher",
                "partner_risk__stock_reserve__rel"],
    "data": ["wizard/sale_advance_payment_wzd_view.xml",
             "sale_view.xml",
             "wizard/apply_on_account_amount_view.xml",
             "invoice_view.xml",
             "partner_view.xml",
             "security/ir.model.access.csv"],
    "installable": True,
}
