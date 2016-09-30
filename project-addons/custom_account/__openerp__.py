# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
    'name': 'Account custom',
    'version': '1.0',
    'category': 'account',
    'description': """
        Account customizations:
            -Relation between stock.move and account.invoice.line
            -Attach the picking report in invoice email.
    """,
    'author': 'Pexego',
    'website': '',
    "depends": ['email_template', 'report', 'account', 'stock', 'product_brand',
                'stock_account', 'sale_stock', 'account_payment_partner', 'crm',
                'account_payment', 'sale', 'purchase', 'nan_partner_risk',
                'sale_margin_percentage', 'account_banking_sepa_direct_debit',
                'account_banking_payment_export', 'stock_reserve_sale',
                'custom_partner', 'sale_quick_payment',
                'account_direct_debit_with_refunds'],
    "data": ['account_view.xml',
             'partner_view.xml',
             'report/account_invoice_report_view.xml',
             'report_custom_view.xml',
             'security/ir.model.access.csv',
             'stock_view.xml',
             'account_payment.xml',
             'crm_view.xml',
             'purchase_view.xml',
             'product_view.xml',
             'report/sale_report_view.xml'],
    "installable": True
}
