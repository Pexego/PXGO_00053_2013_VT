##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from odoo import fields, models


class product_category(models.Model):
    _inherit = "product.category"
    property_account_creditor_price_difference_categ = fields.Many2one(
            'account.account', string="Price Difference Account",
            company_dependent=True,
            help="This account will be used to value price difference between purchase price and cost price.")


class product_template(models.Model):
    _inherit = "product.template"

    property_account_creditor_price_difference = fields.Many2one(
            'account.account', string="Price Difference Account", company_dependent=True,
            help="This account will be used to value price difference between purchase price and cost price.")
