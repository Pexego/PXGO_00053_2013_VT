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

from openerp import models, fields, api


class purchase_order(models.Model):

    _inherit = 'purchase.order'

    picking_created = fields.Boolean('Picking created',
                                     compute='is_picking_created')

    @api.multi
    def test_moves_done(self):
        '''PO is done at the delivery side if all the incoming shipments
           are done'''
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
        purchase_line_obj = self.pool['purchase.order.line']
        res = super(purchase_order, self)._prepare_order_line_move(
            cr, uid, order, order_line, picking_id, group_id, context)
        for move_dict in res:
            move_dict.pop('picking_id', None)
            move_dict.pop('product_uos_qty', None)
            move_dict.pop('product_uos', None)
            move_dict['partner_id'] = order.partner_id.id
            if order.partner_ref:
                move_dict['origin'] += ":" + order.partner_ref
            if move_dict.get('purchase_line_id', False):
                purchase_line = purchase_line_obj.\
                    browse(cr, uid, move_dict['purchase_line_id'])
                if purchase_line.discount:
                    price_unit = order_line.price_unit * \
                        (1 - order_line.discount / 100.0)
                    if order_line.taxes_id:
                        taxes = self.pool['account.tax'].\
                            compute_all(cr, uid, order_line.taxes_id,
                                        price_unit, 1.0,
                                        order_line.product_id,
                                        order.partner_id)
                        price_unit = taxes['total']
                    if order_line.product_uom.id != \
                            order_line.product_id.uom_id.id:
                        price_unit *= order_line.product_uom.factor / \
                            order_line.product_id.uom_id.factor
                    if order.currency_id.id != order.company_id.currency_id.id:
                        price_unit = self.pool.get('res.currency').\
                            compute(cr, uid, order.currency_id.id,
                                    order.company_id.currency_id.id,
                                    price_unit, round=False, context=context)
                    move_dict['price_unit'] = price_unit
        return res

    def action_picking_create(self, cr, uid, ids, context=None):
        """
            Se sobreescribe la función para que no se cree el picking.
        """
        for order in self.browse(cr, uid, ids):
            self._create_stock_moves(cr, uid, order, order.order_line,
                                     False, context=context)

    def _create_stock_moves(self, cr, uid, order, order_lines,
                            picking_id=False, context=None):
        """
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


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def write(self, vals):
        res = super(purchase_order_line, self).write(vals)
        for line in self:
            if line.move_ids and vals.get('date_planned', False):
                for move in line.move_ids:
                    if not (move.state == u'cancel'
                            or move.state == u'done'):
                        move.date_expected = vals['date_planned']
        return res
