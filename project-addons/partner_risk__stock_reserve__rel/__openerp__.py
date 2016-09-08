# -*- coding: utf-8 -*-
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
    'name': "Relation between nan_partner_risk and sale_reserve module",
    'version': '1.0',
    'category': 'sale',
    'description': """Add a relationship between partner_risk and sale_reserve to the sales workflow is not overwritted""",
    'author': 'Pexego Sistemas Informáticos',
    'website': 'www.pexego.es',
    "depends": ['sale',
                'sale_stock',
                'nan_partner_risk',
                'stock_reserve',
                'stock_reserve_sale',
                'sale_quick_payment'],
    "data": ['sale_workflow.xml',
             'sale_view.xml'],
    "installable": True
}
