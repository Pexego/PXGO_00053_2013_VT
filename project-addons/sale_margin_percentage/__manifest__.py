##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
    'name': 'Percentage of margins in Sales Orders',
    'version': '1.0',
    'category': 'Sales Management',
    'description': """
    """,
    'author': 'Pexego',
    'depends': ['sale',
                'stock_deposit',
                'rappel'
                # 'pmp_landed_costs'
                ],
    'data': ["views/sale_view.xml", "views/sale_report_view.xml"],
    'auto_install': False,
    'installable': True,
}
