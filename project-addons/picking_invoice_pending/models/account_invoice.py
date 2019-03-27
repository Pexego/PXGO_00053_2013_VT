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

    @api.multi
    def action_cancel(self):
        ret = super().action_cancel()
        if ret:
            move_line_obj = self.env['account.move.line']
            for inv in self:
                for picking in inv.picking_ids:
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
                for picking in inv.picking_ids:
                    if picking.pending_invoice_move_id:
                        date = (inv.date or
                                inv.date_invoice or fields.Date.today())
                        picking.pending_invoice_move_id.\
                            create_reversals(date, reconcile=True)

        return ret
