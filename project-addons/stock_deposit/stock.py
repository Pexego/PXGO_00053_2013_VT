# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Santi Argüeso
#    Copyright 2014 Pexego Sistemas Informáticos S.L.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from odoo import models, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
from datetime import datetime, timedelta


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_done(self):
        res = super(stock_move, self).action_done()
        deposit_obj = self.env['stock.deposit']
        for move in self:
            if move.procurement_id.sale_line_id.deposit and \
                    move.picking_type_id.code == "outgoing":
                formatted_date = datetime.strptime(time.strftime('%Y-%m-%d'),
                                                   "%Y-%m-%d")
                return_date = datetime.\
                    strftime(formatted_date + timedelta(days=15), "%Y-%m-%d")
                values = {
                    'move_id': move.id,
                    'delivery_date':
                    time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'return_date':
                    move.procurement_id.sale_line_id.deposit_date or
                    return_date,
                    'user_id':
                    move.procurement_id.sale_line_id.order_id.user_id.id,
                    'state': 'draft'
                }
                deposit_obj.create(values)
        return res


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _invoice_create_line(self, moves, journal_id, inv_type='out_invoice'):
        moves_invoice = self.env['stock.move']
        for move in moves:
            if move.procurement_id.sale_line_id.deposit and \
                    move.location_id.usage == 'internal':
                move.invoice_state = 'invoiced'
                continue
            moves_invoice += move
        return super(stock_picking, self)._invoice_create_line(
            moves_invoice, journal_id, inv_type)

    @api.multi
    def action_assign(self):
        for picking in self:
            all_deposit = True
            for move in picking.move_lines:
                if not move.procurement_id.sale_line_id.deposit:
                    all_deposit = False
            if all_deposit and picking.invoice_state == '2binvoiced':
                picking.invoice_state = 'invoiced'
        return super(stock_picking, self).action_assign()

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        res = super(stock_picking, self)._get_invoice_vals(key, inv_type, journal_id, move)
        if 'comment' in res:
            res.pop('comment', None)
        return res

'''class stock_invoice_onshipping(models.TransientModel):

    _inherit = 'stock.invoice.onshipping'

    @api.multi
    def open_invoice(self):
        invoice_ids = self.create_invoice()
        if not invoice_ids:
            return True

        action = {}

        journal2type = {'sale': 'out_invoice', 'purchase': 'in_invoice',
                        'sale_refund': 'out_refund',
                        'purchase_refund': 'in_refund'}
        inv_type = journal2type.get(self.journal_type) or 'out_invoice'
        if inv_type == "out_invoice":
            action = self.env.ref('account.action_invoice_tree1')
        elif inv_type == "in_invoice":
            action = self.env.ref('account.action_invoice_tree2')
        elif inv_type == "out_refund":
            action = self.env.ref('account.action_invoice_tree3')
        elif inv_type == "in_refund":
            action = self.env.ref('account.action_invoice_tree4')

        if action:
            act_data = action.read()
            act_data['domain'] = "[('id','in', [" + \
                ','.join(map(str, invoice_ids)) + "])]"
            return action
        return True'''
