# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego S.I. (<http://www.pexego.es>).
#
#    All other contributions are (C) by their respective contributors
#
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
    'name': 'Account Banking - Export sepa direct debit grouping by partner',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Banking addons community',
    'website': 'https://launchpad.net/banking-addons',
    'category': 'Banking addons',
    'depends': ['account_banking_sepa_direct_debit',
                'account_banking_payment_export',
                'account_payment',
                'account_banking_payment_transfer'],
    'data': ['wizard/export_sdd_view.xml',
             'payment_order_data.xml'],
    'demo': [],
    'description': '''
Allow to export sepa direct debit files grouped by partner.
Send email to partners when payment order is done''',
    'installable': True,
}
