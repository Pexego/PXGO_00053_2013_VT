##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    @author Alberto Luengo Cabanillas
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
    'name': "VIES timestamp",
    'version': '11.0',
    'category': 'visiotech',
    'description': """Adds a VIES validation timestamp when confirming sale orders. Needs installed 'suds' library before.""",
    'author': 'Alberto Luengo para Comunitea',
    'website': 'luengocabanillas.com',
    "depends": ['sale',
                # TODO migrar 'partner_risk__stock_reserve__rel'
                ],
    "data": ['views/sale_order_view.xml',
             'views/fiscal_position_view.xml'],
    "installable": True
}
