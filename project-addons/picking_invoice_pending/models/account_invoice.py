##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from odoo import models, api, fields


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    invoice_created_from_picking = fields.Boolean(readonly=True, copy=False)

    @api.multi
    def action_cancel(self):
        ret = super().action_cancel()
        if ret:
            for inv in self:
                purchase_lines = inv.invoice_line_ids.\
                    mapped('purchase_line_id')
                if purchase_lines:
                    moves = self.env['stock.move'].search([
                        ('purchase_line_id', '=', purchase_lines.ids),
                        ('state', '=', 'done')])
                    for picking in moves.mapped('picking_id'):
                        if picking.pending_invoice_move_id:
                            if picking.pending_invoice_move_id.reversal_id:
                                picking.pending_invoice_move_id.reversal_id.\
                                    line_ids.remove_move_reconcile()
                                picking.pending_invoice_move_id.reversal_id.\
                                    button_cancel()
                                picking.pending_invoice_move_id.reversal_id.\
                                    unlink()

        return ret

    @api.multi
    def action_move_create(self):
        ret = super().action_move_create()
        if ret:
            for inv in self:
                purchase_lines = inv.invoice_line_ids.\
                    mapped('purchase_line_id')
                if purchase_lines:
                    moves = self.env['stock.move'].search([
                        ('purchase_line_id', '=', purchase_lines.ids),
                        ('state', '=', 'done')])
                    for picking in moves.mapped('picking_id'):
                        if picking.pending_invoice_move_id and \
                                (picking.pending_invoice_move_id.
                                 to_be_reversed or not picking.
                                 pending_invoice_move_id.reversal_id):
                            date = (inv.date or
                                    inv.date_invoice or fields.Date.today())
                            picking.pending_invoice_move_id.\
                                create_reversals(date, reconcile=True)

        return ret

    @api.model
    def validate_invoices_created_from_picking(self):
        invoices = self.env['account.invoice'].with_context(bypass_risk=True).\
            search([('invoice_created_from_picking', '=', True),
                    ('state', '=', 'draft'),
                    ('number', '=', False)])
        invoices.action_invoice_open()
