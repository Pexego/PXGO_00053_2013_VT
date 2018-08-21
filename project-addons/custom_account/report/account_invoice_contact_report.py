# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
from openerp import models, fields, tools


class AccountInvoiceContactReport(models.Model):

    _name = 'account.invoice.contact.report'
    _description = "Contact Invoices Statistics"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    number = fields.Char('Number', readonly=True)
    date = fields.Date('Date', readonly=True)
    period_id = fields.Many2one('account.period', 'Period', domain=[('state', '<>', 'done')], readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner Company', readonly=True)
    contact_id = fields.Many2one('res.partner', 'Partner Contact', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Supplier Invoice'),
        ('out_refund', 'Customer Refund'),
        ('in_refund', 'Supplier Refund'),
    ], 'Type', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('open', 'Open'),
        ('paid', 'Done'),
        ('cancel', 'Cancelled')
    ], 'Invoice Status', readonly=True)
    price_total = fields.Float('Total Without Tax', readonly=True)
    benefit = fields.Float('Benefit', readonly=True)

    def _select(self):
        select_str = """
            SELECT  sub.id, sub.number, sub.partner_id, sub.contact_id, 
                    sub.date, sub.period_id, sub.type, sub.state, sub.currency_id,
                    sub.price_total / cr.rate as price_total, sub.benefit
        """
        return select_str

    def _sub_select(self):
        select_str = """
                SELECT  ai.id, ai.number AS number, ai.partner_id, coalesce(rp_contact.id, ai.partner_id) AS contact_id,
                        ai.date_invoice AS date, ai.period_id, ai.type, ai.state, ai.currency_id, 
                        SUM(CASE
                                WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                                THEN - ail.price_subtotal
                                ELSE ail.price_subtotal
                            END) AS price_total,
                        SUM(ail.quantity * ail.price_unit * (100.0-ail.discount) / 100.0) - sum(coalesce(ail.cost_unit, 0)*ail.quantity) as benefit
        """
        return select_str

    def _from(self):
        from_str = """
                FROM account_invoice_line ail
                JOIN account_invoice ai ON ai.id = ail.invoice_id
                LEFT JOIN sale_order_line_invoice_rel solir ON solir.invoice_id = ail.id
                LEFT JOIN sale_order_line sol ON  sol.id = solir.order_line_id
                LEFT JOIN sale_order so ON so.id = sol.order_id
                LEFT JOIN res_partner rp_contact ON rp_contact.id = so.partner_shipping_id 
        """
        return from_str

    def _group_by(self):
        group_by_str = """
                GROUP BY ai.id, ai.partner_id, coalesce(rp_contact.id, ai.partner_id), ai.number, ai.date_invoice, ai.period_id,
                      ai.currency_id, ai.type, ai.state
        """
        return group_by_str

    def init(self, cr):
        # self._table = account_invoice_contact_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            WITH currency_rate (currency_id, rate, date_start, date_end) AS (
                SELECT r.currency_id, r.rate, r.name AS date_start,
                    (SELECT name FROM res_currency_rate r2
                     WHERE r2.name > r.name AND
                           r2.currency_id = r.currency_id
                     ORDER BY r2.name ASC
                     LIMIT 1) AS date_end
                FROM res_currency_rate r
            )
            %s
            FROM (
                %s %s %s
            ) AS sub
            JOIN currency_rate cr ON
                (cr.currency_id = sub.currency_id AND
                 cr.date_start <= COALESCE(sub.date, NOW()) AND
                 (cr.date_end IS NULL OR cr.date_end > COALESCE(sub.date, NOW())))
        )""" % (
                    self._table,
                    self._select(), self._sub_select(), self._from(), self._group_by()))

