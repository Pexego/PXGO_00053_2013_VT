# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedrar <omar@comunitea.com>$
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
    'name': 'CyC report',
    'version': '1.0',
    'category': '',
    'description': "Shows the invoices grouped by country and year for "
                   "export",
    'author': 'Comunitea',
    'website': '',
    "depends": ['account', 'account_payment_partner', 'customer_area',
                'account_followup'],
    "data": ['account_invoice_cyc_view.xml',
             'security/ir.model.access.csv',
             'account_view.xml'],
    "installable": True
}
