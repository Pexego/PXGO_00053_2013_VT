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
    'name': 'Add payment mode to payment terms',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Banking addons community',
    'website': 'https://launchpad.net/banking-addons',
    'category': 'Banking addons',
    'depends': ['account', 'account_payment', 'account_payment_return'],
    'data': ['views/account_view.xml'],
    'description': '''
Allow to set a preferer payment mode on payment term lines. Only informative
on invoices''',
    'installable': True,
}
