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
from dateutil.relativedelta import relativedelta


class Partner(models.Model):

    _inherit = "res.partner"

    email2 = fields.Char('Second Email')
    not_send_following_email = fields.Boolean()

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

    @api.multi
    def _get_valid_followup_partners(self):
        company_id = self.env.user.company_id.id
        partners = self.env['res.partner']
        period = self.env['account.period']
        ctx2 = dict(self.env.context)
        search_date = (date.today() + relativedelta(days=6)).\
            strftime("%Y-%m-%d")
        ctx2['date_to'] = search_date
        ctx2['date_from'] = search_date[:4] + "-01-01"

        ctx3 = dict(ctx2)
        ctx3['initial_bal'] = True
        for partner in self:
            global_balance = partner.credit + partner.debit
            init_balance = partner.with_context(ctx3).credit + \
                partner.with_context(ctx3).debit
            balance_in_date = partner.with_context(ctx2).credit + \
                partner.with_context(ctx2).debit
            if global_balance >=5 and (balance_in_date + init_balance) >=5 \
                    and not partner.not_send_following_email:
                if self.env['account.move.line'].search(
                    [('partner_id', '=', partner.id),
                     ('account_id.type', '=', 'receivable'),
                     ('reconcile_id', '=', False),
                     ('state', '!=', 'draft'),
                     ('company_id', '=', company_id),
                     ('blocked', '!=', True),
                     '|', ('date_maturity', '=', False),
                     ('date_maturity', '<=', search_date)]):
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


    @api.onchange("user_id")
    def on_change_user_id(self):
        if self.user_id and self.user_id.default_section_id:
            self.section_id = self.user_id.default_section_id.id
