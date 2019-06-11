# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from datetime import timedelta, date


class ResPartner(models.Model):

    _inherit = "res.partner"

    blocked_sales = fields.Boolean('Sales blocked?', copy=False)
    defaulter = fields.Boolean()

    def get_partners_to_check(self):
        partners_to_check = self
        if self.commercial_partner_id != self:
            partners_to_check += self.commercial_partner_id
        return partners_to_check

    @api.model
    def check_customer_blocked_sales(self):
        """
        Buscamos todos los asientos contables de aquellas facturas de cliente
        que no estén pagadas que posean una fecha de vencimiento anterior
        a la fecha actual+periodo de gracia configurable en la compañia...
        """
        visited_partner_ids = []
        limit_customer_date = fields.Date.to_string(
            date.today() + timedelta(days=-int(
                self.env.user.company_id.block_customer_days)))

        # Buscamos efectos no conciliados, con fecha anterior a la fecha
        # limite, de tipo 'receivable'
        cust_account = self.env['account.account'].search(
            [('company_id', '=', self.env.user.company_id.id),
             ('internal_type', '=', 'receivable'),
             ('code', 'like', '430%')])
        move_lines = self.env['account.move.line'].search(
            [('account_id', 'in', cust_account._ids),
             ('date_maturity', '<', limit_customer_date),
             ('full_reconcile_id', '=', False)])
        if len(move_lines) > 0:
            for move_line in move_lines:
                if move_line.partner_id.id not in visited_partner_ids:
                    visited_partner_ids.append(move_line.partner_id.id)
                    move_line.partner_id.check_customer_block_state()
        other_partner_ids = self.env['res.partner'].search(
            [('blocked_sales', '=', True),
             ('id', 'not in', visited_partner_ids)])
        if other_partner_ids:
            other_partner_ids.write({'blocked_sales': False})

    def check_customer_block_state(self):
        limit_customer_date = fields.Date.to_string(
            date.today() + timedelta(days=-int(
                self.env.user.company_id.block_customer_days)))
        for partner in self:
            cust_accounts = self.env['account.account'].search(
                [('company_id', '=', self.env.user.company_id.id),
                 ('internal_type', '=', 'receivable'),
                 ('code', 'like', '430%')])
            move_lines = self.env['account.move.line'].search(
                [('account_id', 'in', cust_accounts._ids),
                 '|', ('date_maturity', '<', limit_customer_date),
                 ('date_maturity', '=', False),
                 ('full_reconcile_id', '=', False),
                 ('partner_id', '=', partner.id)])
            balance = 0
            for line in move_lines:
                balance += line.credit
                balance -= line.debit
                balance = round(balance, 2)

            if move_lines and balance < 0 and \
                    partner.payment_amount_due > 0:
                partner.write({'blocked_sales': True})
            else:
                partner.write({'blocked_sales': False})

        return True
