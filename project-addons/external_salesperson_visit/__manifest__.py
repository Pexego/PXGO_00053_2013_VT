##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
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
    'name': 'Partner Visit',
    'version': '1.0',
    'category': 'Custom',
    'description': """
        External Salesperson Visit
    """,
    'author': 'Nadia Ferreyra',
    'website': '',
    'depends': ['base',
                'mail',
                'crm',
                'customer_area',
                'custom_partner',
                ],
    'data': ['views/partner_visit_view.xml',
             'data/email_template.xml',
             'security/ir.model.access.csv',
             'security/external_salesperson_visit_security.xml'
             ],
    'installable': True
}
