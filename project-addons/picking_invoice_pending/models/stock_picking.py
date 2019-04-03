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

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class StockPicking(models.Model):

    _inherit = "stock.picking"

    pending_invoice_move_id = fields.Many2one('account.move',
                                              'Account pending move',
                                              readonly=True,
                                              copy=False)
    pending_stock_reverse_move_id = \
        fields.Many2one('account.move', 'Account pending stock reverse move',
                        readonly=True, copy=False)
    pending_stock_move_id = \
        fields.Many2one('account.move', 'Account pending stock move',
                        readonly=True, copy=False)

    @api.multi
    def account_pending_invoice(self, debit_account, credit_account, date):
        self.ensure_one()
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        lines = {}

        origin = self.name
        if self.origin:
            origin += ':' + self.origin

        stock_journal_id = self.company_id.property_pending_stock_journal.id

        move = {
            'ref': origin,
            'journal_id': stock_journal_id,
            'date': date,
        }
        move_id = move_obj.create(move)
        lines_data = []
        obj_precision = self.env['decimal.precision']
        for move_line in self.move_lines:
            name = move_line.name or origin

            amount_line = round(move_line._get_price_unit(), obj_precision.
                                precision_get('Account')) * \
                move_line.product_qty
            vals = {
                'name': name,
                'ref': origin,
                'partner_id': move_line.partner_id.commercial_partner_id.id,
                'product_id': move_line.product_id.id,
                'account_id': debit_account.id,
                'debit': amount_line,
                'credit': 0,
                'quantity': move_line.product_qty,
                'move_id': move_id.id,
                'journal_id': stock_journal_id,
                'date': date
            }
            lines_data.append(vals)
            if move_line.partner_id.commercial_partner_id.id in lines:
                lines[move_line.partner_id.commercial_partner_id.id] += \
                    amount_line
            else:
                lines[move_line.partner_id.commercial_partner_id.id] = \
                    amount_line

        for partner_id in lines:
            vals = {
                'name': name,
                'ref': origin,
                'partner_id': partner_id,
                'account_id': credit_account.id,
                'debit': 0,
                'credit': round(lines[partner_id], obj_precision.
                                precision_get('Account')),
                'move_id': move_id.id,
                'journal_id': stock_journal_id,
                'date': date,
            }
            lines_data.append(vals)
        move_id.line_ids = [(0, 0, x) for x in lines_data]
        move_id.post()

        return move_id

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if vals.get('date_done'):
            inv_type = 'out_invoice'
            ctx = dict(self._context or {})
            ctx['date_inv'] = False
            ctx['inv_type'] = inv_type
            for pick in self:
                if (pick.picking_type_id.code == "incoming" and pick.move_lines
                        and pick.move_lines[0].purchase_line_id and
                        pick.company_id.required_invoice_pending_move and
                        not pick.pending_stock_reverse_move_id):
                    pick.refresh()
                    if not pick.company_id.\
                            property_pending_variation_account or not \
                            pick.company_id.property_pending_stock_account:
                        raise Warning(_("You need to configure the accounts "
                                        "in the company for pending invoices"))
                    if not pick.company_id.property_pending_stock_journal:
                        raise Warning(_("You need to configure an account "
                                        "journal in the company for pending "
                                        "invoices"))
                    debit_account = pick.company_id.\
                        property_pending_variation_account
                    credit_account = pick.company_id.\
                        property_pending_stock_account
                    change_date = vals['date_done']
                    if pick.backorder_id:
                        change_date = pick.backorder_id.date_done
                    move_id = pick.account_pending_invoice(debit_account,
                                                           credit_account,
                                                           change_date)
                    pick.pending_stock_reverse_move_id = move_id.id

        return res

    @api.multi
    def action_confirm(self):
        res = super().action_confirm()
        for pick in self:
            if not pick.company_id. \
                    property_pending_variation_account or not \
                    pick.company_id.property_pending_stock_account or not \
                    pick.company_id.property_pending_supplier_invoice_account:
                raise Warning(_("You need to configure the accounts "
                                "in the company for pending invoices"))
            if not pick.company_id.property_pending_stock_journal:
                raise Warning(_("You need to configure an account "
                                "journal in the company for pending "
                                "invoices"))

            if pick.pickiwng_type_id.code == "incoming" and pick.move_lines \
                    and pick.move_lines[0].purchase_line_id and \
                    pick.company_id.required_invoice_pending_move and \
                    not pick.backorder_id and \
                    not pick.pending_invoice_move_id and \
                    not pick.pending_stock_move_id:
                debit_account = pick.company_id.\
                    property_pending_expenses_account
                credit_account = pick.company_id.\
                    property_pending_supplier_invoice_account
                move_id = pick.account_pending_invoice(debit_account,
                                                       credit_account,
                                                       pick.create_date[:10])
                pick.pending_invoice_move_id = move_id.id

                debit_account = pick.company_id.\
                    property_pending_stock_account
                credit_account = pick.company_id.\
                    property_pending_variation_account
                move_id = pick.account_pending_invoice(debit_account,
                                                       credit_account,
                                                       pick.create_date[:10])
                pick.pending_stock_move_id = move_id.id

        return res

    @api.multi
    def action_cancel(self):
        res = super().action_cancel()
        for pick in self:
            if pick.pending_stock_move_id:
                pick.pending_stock_move_id.button_cancel()
                pick.pending_stock_move_id.unlink()
            if pick.pending_invoice_move_id:
                pick.pending_invoice_move_id.button_cancel()
                pick.pending_invoice_move_id.unlink()
            if pick.pending_stock_reverse_move_id:
                pick.pending_stock_reverse_move_id.button_cancel()
                pick.pending_stock_reverse_move_id.unlink()
        return res

    @api.multi
    def unlink(self):
        for pick in self:
            if pick.pending_stock_move_id:
                pick.pending_stock_move_id.button_cancel()
                pick.pending_stock_move_id.unlink()
            if pick.pending_invoice_move_id:
                pick.pending_invoice_move_id.button_cancel()
                pick.pending_invoice_move_id.unlink()
            if pick.pending_stock_reverse_move_id:
                pick.pending_stock_reverse_move_id.button_cancel()
                pick.pending_stock_reverse_move_id.unlink()
        return super().unlink()

    # TODO: Migrar
    # ~ @api.model
    # ~ def cron_create_invoices(self):
        # ~ picking_obj = self.env['stock.picking']
        # ~ journal_obj = self.env['account.journal']
        # ~ journal_id = journal_obj.search([('type', '=', 'sale')])[0].id
        # ~ inv_type = 'out_invoice'
        # ~ ctx = dict(self._context or {})
        # ~ ctx['date_inv'] = False
        # ~ ctx['inv_type'] = inv_type
        # ~ templates = []
        # ~ validate = True

        # ~ # Deliveries to Invoice
        # ~ pickings = picking_obj.with_context(ctx).search([('state', '=', 'done'),
                                                         # ~ ('invoice_state', '=', '2binvoiced'),
                                                         # ~ ('invoice_type_id.name', '=', 'Diaria'),
                                                         # ~ ('picking_type_id.code', '=', 'outgoing'),
                                                         # ~ ('tests', '=', False)],
                                                        # ~ order='date_done')

        # ~ # Create invoice
        # ~ res = pickings.action_invoice_create(journal_id=journal_id, group=False, type=inv_type)
        # ~ invoices_created = self.env['account.invoice'].browse(res)
        # ~ if len(pickings) != len(res):
            # ~ templates.append(self.env.ref('picking_invoice_pending.alert_cron_create_invoices', False))
        # ~ if len(res) != len(invoices_created.mapped('invoice_line.invoice_id.id')):
            # ~ # There are invoices created without lines
            # ~ templates.append(self.env.ref('picking_invoice_pending.alert_cron_create_invoices_empty_lines', False))
            # ~ # Do not validate them because it will generate an error
            # ~ validate = False
        # ~ if validate:
            # ~ # Validate invoice
            # ~ invoices_created.signal_workflow('invoice_open')
            # ~ invoice_states = invoices_created.mapped('state')
            # ~ if 'draft' in invoice_states or 'cancel' in invoice_states or \
                    # ~ 'proforma' in invoice_states or 'proforma2' in invoice_states:
                # ~ templates.append(self.env.ref('picking_invoice_pending.alert_cron_validate_invoices', False))

        # ~ for tmpl in templates:
            # ~ ctx.update({
                # ~ 'default_model': 'account.invoice',
                # ~ 'default_res_id': invoices_created[0].id,
                # ~ 'default_use_template': bool(tmpl.id),
                # ~ 'default_template_id': tmpl.id,
                # ~ 'default_composition_mode': 'comment',
                # ~ 'mark_so_as_sent': True
            # ~ })
            # ~ composer_id = self.env['mail.compose.message'].with_context(ctx).create({})
            # ~ composer_id.with_context(ctx).send_mail()

        # ~ return True
