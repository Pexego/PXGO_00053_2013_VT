# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
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

from openerp import models, fields, api, _


class purchase_order(models.Model):

    _inherit = 'purchase.order'

    picking_created = fields.Boolean('Picking created', compute='is_picking_created')

    @api.multi
    def test_moves_done(self):
        '''PO is done at the delivery side if all the incoming shipments are done'''
        for purchase in self:
            for line in purchase.order_line:
                for move in line.move_ids:
                    if move.state != 'done':
                        return False
        return True

    def is_picking_created(self):
        self.picking_created = self.picking_ids and True or False

    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id,
                                 group_id, context=None):
        """
            prepare the stock move data from the PO line.
            This function returns a list of dictionary ready to be used in
            stock.move's create()
        """
        res = super(purchase_order, self)._prepare_order_line_move(
            cr, uid, order, order_line, picking_id, group_id, context)
        for move_dict in res:
            move_dict.pop('picking_id', None)
            move_dict.pop('product_uos_qty', None)
            move_dict.pop('product_uos', None)
            move_dict['partner_id'] = order.partner_id.id
        return res

    def action_picking_create(self, cr, uid, ids, context=None):
        """
            Se sobreescribe la función para que no se cree el picking.
        """
        for order in self.browse(cr, uid, ids):
            self._create_stock_moves(cr, uid, order, order.order_line,
                                     False, context=context)

    def _create_stock_moves(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Creates appropriate stock moves for given order lines, whose can optionally create a
        picking if none is given or no suitable is found, then confirms the moves, makes them
        available, and confirms the pickings.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise a standard
        incoming picking will be created to wrap the stock moves (default behavior of the stock.move)

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: purchase order to which the order lines belong
        :param list(browse_record) order_lines: purchase order line records for which picking
                                                and moves should be created.
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if omitted.
        :return: None

        MOD: Se sobreescribe la función para no confirmar los movimientos.
        """
        stock_move = self.pool.get('stock.move')
        todo_moves = []
        new_group = self.pool.get("procurement.group").create(
            cr, uid, {'name': order.name, 'partner_id': order.partner_id.id},
            context=context)

        for order_line in order_lines:
            if not order_line.product_id:
                continue

            if order_line.product_id.type in ('product', 'consu'):
                for vals in self._prepare_order_line_move(
                        cr, uid, order, order_line, picking_id, new_group,
                        context=context):
                    move = stock_move.create(cr, uid, vals, context=context)
                    todo_moves.append(move)
