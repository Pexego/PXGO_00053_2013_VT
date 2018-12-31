# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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

from openerp import models, fields, tools


class commission_report(models.Model):

    _name = "commission.report"
    _description = "Sale commission report"
    _auto = False

    product_id = fields.Many2one('product.product', 'Product')
    agent_id = fields.Many2one('res.partner', 'Agent')
    qty = fields.Float('Quantity')
    settled = fields.Boolean('Settled')
    inv_date = fields.Date('Date invoice')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT c_line.id,
                i_line.product_id  AS product_id,
                c_line.agent  AS agent_id,
                c_line.amount  AS qty,
                c_line.settled  AS settled,
                inv.date_invoice  AS inv_date,
                inv.state  AS state
            FROM account_invoice_line AS i_line
                JOIN account_invoice_line_agent  AS c_line ON i_line.id=c_line.object_id
                JOIN account_invoice  AS inv ON i_line.invoice_id=inv.id
            WHERE inv.state IN ('open', 'paid')
            GROUP BY i_line.product_id, c_line.agent, c_line.amount, c_line.settled, inv.date_invoice, inv.state, c_line.id
        )""" % (self._table,))
