# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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
    'name': "Flask middleware connector",
    'version': '1.0',
    'category': 'Connector',
    'description': """Connect to Visiotech flask middleware using Odoo connector""",
    'author': 'Comunitea',
    'website': 'www.comunitea.com',
    "depends": ['base', 'product', 'connector', 'stock', 'custom_partner', 'crm_claim_rma'],
    "data": ["views/middleware_view.xml", "views/product_view.xml", 'views/res_users.xml',
             "views/product_brand.xml", "security/ir.model.access.csv"],
    "installable": True
}
