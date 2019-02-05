# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saaevdra <omar@comunitea.com>$
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

from openerp import models, fields, api


class ResPartner(models.Model):

    _inherit = "res.partner"

    @api.one
    def _get_on_account_pur_amount(self):
        amount = 0.0
        voucher_obj = self.env["account.voucher"]
        move_line_obj = self.env["account.move.line"]
        voucher_ids = voucher_obj.search([("type", "=", "payment"),
                                          ("purchase_id", "!=", False),
                                          ("purchase_id.state", "=", "cancel"),
                                          ("partner_id", "=", self.id)])
        move_ids = []
        for voucher in voucher_ids:
            for move in voucher.move_ids:
                if move.account_id.internal_type in ('receivable', 'payable') and \
                        not move.full_reconcile_id:
                    move_ids.append(move.id)
                    if move.reconcile_partial_id:
                        amount += move.amount_residual_currency > 0 and \
                            move.amount_residual_currency or 0.0
                    else:
                        amount += move.amount_currency or move.debit

        moves = move_line_obj.search([('id', 'not in', move_ids),
                                      ('partner_id', '=', self.id),
                                      ('debit', '>', 0.0),
                                      ('full_reconcile_id', '=', False),
                                      ('account_id.internal_type', '=', 'payable')])

        for move in moves:
            vouchers = voucher_obj.search([('move_id', '=', move.move_id.id),
                                           ('purchase_id', '!=', False)])
            if not vouchers:
                if move.reconcile_partial_id:
                    amount += move.amount_residual_currency > 0 and \
                        move.amount_residual_currency or 0.0
                else:
                    amount += move.amount_currency or move.debit

        self.on_account_purchase = amount

    on_account_purchase = fields.Float("Purchase on account amount",
                                       readonly=True,
                                       compute="_get_on_account_pur_amount")
    #TODO: Migrar
    # ~ supplier_currency = fields.Many2one(
        # ~ 'res.currency',
        # ~ related='property_product_pricelist_purchase.currency_id',
        # ~ readonly=True)


class ResCompany(models.Model):

    _inherit = "res.company"

    purchase_advance_payment_account = \
        fields.Many2one('account.account',
                        string="Purchase advance payment account",
                        domain="[('internal_type', '=', 'payable')]")


# TODO: Migrar
# ~ class AccountConfigSettings(models.TransientModel):

    # ~ _inherit = 'account.config.settings'

    # ~ purchase_advance_payment_account = fields.\
        # ~ Many2one('account.account',
                 # ~ related='company_id.purchase_advance_payment_account',
                 # ~ string="Purchase advance payment account",
                 # ~ domain="[('internal_type', '=', 'payable'),"
                        # ~ "('company_id', '=', company_id)]")
