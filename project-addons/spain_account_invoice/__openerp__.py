# -*- coding: utf-8 -*-
###############################################################################
#
#   report_aged_partner_xls for Odoo
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
# -*- coding: utf-8 -*-
# © 2017 Visiotech - Jesús García <jgmanzanas@visiotech.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Invoices export XLS",
    "version": "8.0.1.0.0",
    'author': 'Jesús García Manzanas',
    'website': 'http://www.visiotech.es',
    "category": "Accounting / Reports",
    'depends': [
        'account',
        'account_invoice_currency',
        'report_xlsx',
    ],
    'external_dependencies': {
        'python': ['xlwt'],
    },
    'data': [
        'report/export_invoice_xls.xml',
        'wizard/xls_invoice_report_wizard.xml',
    ],
    'installable': False, # TODO: Migrar
}
