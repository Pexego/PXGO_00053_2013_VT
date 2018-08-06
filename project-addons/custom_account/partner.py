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
    unreconciled_purchase_aml_ids = fields.One2many('account.move.line', 'partner_id',
                                                    domain=['&', ('reconcile_id', '=', False), '&',
                                                            ('account_id.active', '=', True), '&',
                                                            ('account_id.type', '=', 'payable'), '&',
                                                            ('account_id.not_payment_followup', '=', False),
                                                            ('state', '!=', 'draft')])

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
        for partner in self:
            global_balance = partner.credit - partner.debit
            balance = 0.0
            if global_balance >=5 and not partner.not_send_following_email:
                line_ids = self.env['account.move.line'].\
                    search([('partner_id', '=', partner.id),
                            ('account_id.type', '=', 'receivable'),
                            ('reconcile_id', '=', False),
                            ('state', '!=', 'draft'),
                            ('company_id', '=', company_id),
                            ('blocked', '!=', True),
                            '|', ('date_maturity', '=', False),
                            ('date_maturity', '<=', search_date)])
                for line in line_ids:
                    balance += (line.debit - line.credit)
                if balance >= 5:
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
        self.payment_responsible_id = self.user_id.id
        if self.user_id and self.user_id.default_section_id:
            self.section_id = self.user_id.default_section_id.id

    @api.multi
    def action_done(self):
        context = dict(self._context or {})
        if 'params' in context:
            context['params']['not_change_payment_responsible'] = True
        return super(Partner, self).action_done(context=context)

    @api.multi
    def write(self, vals):
        context = self.env.context
        if 'params' in context and context['params'].get('not_change_payment_responsible', False):
            vals.pop('payment_responsible_id')
        return super(Partner, self).write(vals)

