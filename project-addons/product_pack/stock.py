# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp.osv import fields, orm
from openerp import api


class stock_pciking(orm.Model):

    _inherit = 'stock.picking'

    def _has_packs(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for pick in self.browse(cr, uid, ids, context):
            res[pick.id] = False
            for line in pick.move_lines:
                if line.pack_component:
                    res[pick.id] = True
                    break
        return res

    _columns = {
        'has_packs': fields.function(_has_packs, string='Packs',
                                     type='boolean'),
    }

    def action_invoice_create(self, cr, uid, ids, journal_id, group=False,
                              type='out_invoice', context=None):
        """ Creates invoice based on the invoice state selected for picking.
        @param journal_id: Id of journal
        @param group: Whether to create a group invoice or not
        @param type: Type invoice to be created
        @return: Ids of created invoices for the pickings
        """
        context = context or {}
        inv_line_obj = self.pool.get('account.invoice.line')
        todo = {}
        for picking in self.browse(cr, uid, ids, context=context):
            partner = self._get_partner_to_invoice(cr, uid, picking,
                                                   dict(context,
                                                        inv_type=type))
            #grouping is based on the invoiced partner
            if group:
                key = partner
            else:
                key = picking.id
            for move in picking.move_lines:
                if move.invoice_state == '2binvoiced':
                    if (move.state != 'cancel') and not move.scrapped:
                        todo.setdefault(key, [])
                        todo[key].append(move)
        invoices = []
        for moves in todo.values():
            final_moves = []
            pack_moves = []
            for move in moves:
                if not move.pack_component:
                    final_moves.append(move)
                else:
                    pack_moves.append(move)
            if final_moves:
                invoices += self._invoice_create_line(cr, uid,
                                                      final_moves + pack_moves,
                                                      journal_id, type,
                                                      context=context)
                search_vals = [('invoice_id', 'in', invoices),
                               ('move_id', 'in',
                                [x.id for x in pack_moves])]
                to_delete = inv_line_obj.search(cr, uid, search_vals,
                                                context=context)
                inv_line_obj.unlink(cr, uid, to_delete, context)
            else:
                # Si el albarán no tiene ningun movimiento facturable se crea
                # una factura con uno de los movimientos y se borran las lineas
                invoice = self._invoice_create_line(cr, uid, [moves[0]],
                                                    journal_id, type,
                                                    context=context)
                search_vals = [('invoice_id', '=', invoice),
                               ('product_id', '=', moves[0].product_id.id)]
                to_delete = inv_line_obj.search(cr, uid, search_vals,
                                                context=context)
                inv_line_obj.unlink(cr, uid, to_delete, context)
                invoices += invoice
            if pack_moves:
                self.pool.get('stock.move').\
                    write(cr, uid, [x.id for x in pack_moves],
                          {'invoice_state': 'invoiced'}, context)
        return invoices


class stock_move(orm.Model):

    _inherit = 'stock.move'

    @api.multi
    def get_sale_line_id(self):
        sale_id = self.procurement_id.sale_line_id
        if not sale_id and self.move_dest_id:
            sale_id = self.move_dest_id.get_sale_line_id()
        return sale_id

    def _pack_component(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for move in self.browse(cr, uid, ids, context):
            res[move.id] = False
            if self.get_sale_line_id(cr, uid, move.id, context):
                if self.get_sale_line_id(cr, uid, move.id, context).\
                        pack_parent_line_id:
                    res[move.id] = True
        return res

    _columns = {
        'pack_component': fields.function(_pack_component,
                                          string='pack component',
                                          type='boolean',
                                          store=False),
    }
