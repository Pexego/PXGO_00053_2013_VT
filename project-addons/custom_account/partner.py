# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sanchez <kiko@comunitea.com>$
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
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import date
from openerp import fields, models, api, exceptions, _
from openerp.osv import fields as fields2


class Partner(models.Model):

    _inherit = "res.partner"

    @api.one
    def _pending_orders_amount(self):
        total = 0.0
        moves = self.env['stock.move'].\
            search([('partner_id', 'child_of', [self.id]),
                    ('state', 'not in', ['draft', 'cancel']),
                    ('procurement_id.sale_line_id', '!=', False),
                    ('invoice_state', '=', '2binvoiced')])

        for move in moves:
            line = move.procurement_id.sale_line_id
            sign = move.picking_type_code == "outgoing" and 1 or -1
            total += sign * (move.product_uom_qty * (line.price_unit * (1 - (line.discount or 0.0) / 100.0)))

        lines = self.env['sale.order.line'].\
            search([('order_id.partner_id', 'child_of', [self.id]),
                    ('order_id.state', 'not in',
                     ['draft','cancel','wait_risk','sent',
                      'history', 'reserve']),
                    ('invoiced', '=', False), '|', ('product_id', '=', False),
                    ('product_id.type', '=', 'service')])
        for sline in lines:
            total += sline.price_subtotal

        self.pending_orders_amount = total

    def _get_circulating_amount(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for id in ids:
            amount = 0.0
            move_ids = self.pool.get('account.move.line').\
                search(cr, uid, [('partner_id', 'child_of', [id]),
                                 ('account_id.circulating', '=', True),
                                 ('reconcile_id','=',False)])

            for line in self.pool.get('account.move.line').browse(cr, uid, move_ids, context):
                if line.currency_id:
                    sign = line.amount_currency < 0 and -1 or 1
                else:
                    sign = (line.debit - line.credit) < 0 and -1 or 1
                if line.reconcile_partial_id:
                     amount += line.debit - line.credit
                else:
                    amount += sign * line.amount_residual

            bank_line_ids = self.pool.get("bank.payment.line").\
                search(cr, uid, [('partner_id', 'child_of', [id]),
                                 ('order_id.payment_order_type', '=',
                                  'debit')])
            for bank_line in self.pool.get("bank.payment.line").\
                    browse(cr, uid, bank_line_ids):
                move_line = bank_line.transfer_move_line_id
                if not move_line.reconcile_id and not move_line.partner_id:
                    amount += bank_line.amount_currency

            res[id] = amount

        return res

    _columns = {
        'circulating_amount': fields2.\
            function(_get_circulating_amount, method=True,
                     string="Circulating amount", type="float"),
    }

    @api.multi
    def _get_valid_followup_partners(self):
        company_id = self.env.user.company_id.id
        partners = self.env['res.partner']
        period = self.env['account.period']
        ctx2 = dict(self.env.context)
        ctx2['periods'] = [period.find(date.today())[:1].id]
        for partner in self:
            if partner.credit + partner.debit > 0 and partner.with_context(ctx2).credit + partner.with_context(ctx2).debit >=0:
                if self.env['account.move.line'].search(
                    [('partner_id', '=', partner.id),
                     ('account_id.type', '=', 'receivable'),
                     ('reconcile_id', '=', False),
                     ('state', '!=', 'draft'),
                     ('company_id', '=', company_id),
                     ('blocked', '!=', True),
                     '|', ('date_maturity', '=', False),
                     ('date_maturity', '<=', fields.Date.context_today(self))]):
                    '''raise exceptions.Warning(
                        _('Error!'),
                        _("The partner does not have any accounting entries to print in the overdue report for the current company."))'''
                    partners += partner
        return partners

    @api.multi
    def do_partner_mail(self):
        partners = self._get_valid_followup_partners()
        return super(Partner, partners).do_partner_mail()

    @api.multi
    def do_button_print(self):
        partners = self._get_valid_followup_partners()
        if partners:
            return super(Partner, partners).do_button_print()


    attach_picking = fields.Boolean("Attach picking")
    newsletter = fields.Boolean('Newsletter')
    pending_orders_amount = fields.Float(compute="_pending_orders_amount",
                                         string='Uninvoiced Orders')
    circulating_amount = fields.Float(compute="_get_circulating_amount",
                                      string="Circulating amount")


    @api.onchange("user_id")
    def on_change_user_id(self):
        if self.user_id and self.user_id.default_section_id:
            self.section_id = self.user_id.default_section_id.id
