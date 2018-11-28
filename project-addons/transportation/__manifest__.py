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
    'name': "Transportation",
    'version': '1.0',
    'category': 'sale',
    'description':
    """
        Gestión de transportistas y rotación.
    """,
    'author': 'Pexego Sistemas Informáticos',
    'website': 'www.pexego.es',
    "depends": ['base',
                'sale',
                'customer_area',
                'stock',
                'delivery'],
    "data": ['security/ir.model.access.csv',
             'wizard/picking_tracking_status_view.xml',
             'views/res_partner_view.xml',
             'views/transportation_view.xml',
             'views/sale_view.xml', 'views/stock_view.xml',
             'data/parameters.xml'],
    "installable": True
}
