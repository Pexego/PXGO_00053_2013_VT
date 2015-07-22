# -*- coding: utf-8 -*-
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
    'name': "Block Invoices",
    'version': '1.0',
    'category': 'visiotech',
    'description': """Bloqueo de ventas a clientes configurable. Incluye un cron diario nocturno.""",
    'author': 'Alberto Luengo para Comunitea',
    'website': 'luengocabanillas.com',
    "depends": ['sale','stock_account'],
    "data": ['res_company_view.xml','res_partner_view.xml','data/ir_cron.xml'],
    "installable": True
}
