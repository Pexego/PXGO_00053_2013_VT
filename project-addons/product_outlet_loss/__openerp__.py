# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sánchez <kiko@comunitea.com>$
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
    'name': "Outlet Loss",
    'version': '1.0',
    'category': 'product',
    'description': """Manage outlet products losses.""",
    'author': 'Comunitea Servicios Tecnológicos',
    'website': 'www.comunitea.com',
    "depends": ['base',
                'product',
                'stock',
                'equivalent_products',
                'product_outlet'],
    "data": ['wizard/product_outlet_wizard_view.xml',
             'outlet_loss.xml',
             'res_company.xml',
             'security/ir.model.access.csv'],
    "installable": True
}
