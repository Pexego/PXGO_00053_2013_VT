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

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
import openerp


class stock_deposit(osv.osv):

    _name = 'stock.deposit'
    _inherit = ['mail.thread', 'ir.needaction_mixin']




    _columns = {
        'product_id': fields.related('move_id', 'product_id',
                                     type='many2one',
                                     relation='product.product',
                                     string='Product',
                                     store=True,
                                     select=True,
                                     readonly=True),
        'product_uom_qty': fields.related('move_id', 'product_uom_qty',
                                          type='float',
                                          string='Product qty',
                                          store=True,
                                          select=True,
                                          readonly=True),
        'product_uom': fields.related('move_id', 'product_uom',
                                      type='many2one',
                                      relation='product.uom',
                                      string='Uom',
                                      store=True,
                                      select=True,
                                      readonly=True),
        'move_id': fields.many2one('stock.move',
                                   'Deposit Move',
                                   required=True,
                                   readonly=True,
                                   ondelete='cascade',
                                   select=1),
        'picking_id': fields.related('move_id', 'picking_id',
                                     type='many2one',
                                     relation='stock.picking',
                                     string='Picking',
                                     store=True,
                                     select=True,
                                     readonly=True),
        'partner_id': fields.related('move_id', 'partner_id',
                                     type='many2one',
                                     relation='res.partner',
                                     string='Destination Address',
                                     store=True,
                                     select=True,
                                     readonly=True),

        'delivery_date': fields.datetime('Date of Transfer',),
        'return_date': fields.date('Return date'),
        'company_id': fields.related('move_id', 'company_id',
                                     type='many2one',
                                     relation='res.company',
                                     string='Date of Transfer',
                                     store=True,
                                     select=True,
                                     readonly=True),
        'state': fields.selection([
            ('done', 'Done'),
            ('sale', 'Sale'),
            ('returned', 'Returned')], 'State',
            readonly=True, required=True),
        'sale_move_id': fields.many2one('stock.move',
                                   'Sale Move',
                                   required=False,
                                   readonly=True,
                                   ondelete='cascade',
                                   select=1),
        'return_picking_id': fields.many2one('stock.picking',
                                   'Return Picking',
                                   required=False,
                                   readonly=True,
                                   ondelete='cascade',
                                   select=1),
        'user_id': fields.many2one('res.users',
                                   'Comercial',
                                   required=False,
                                   readonly=True,
                                   ondelete='cascade',
                                   select=1),
    }

    def sale(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('stock.move')
        for deposit in self.browse(cr, uid, ids, context=context):
            values ={
                'product_id': deposit.product_id.id,
                'product_uom_qty': deposit.product_uom_qty,
                'product_uom': deposit.product_uom.id,
                'partner_id': deposit.partner_id.id,
                'name': 'Sale Deposit: ' + deposit.move_id.name,
                'location_id': deposit.move_id.location_dest_id.id,
                'location_dest_id': deposit.partner_id.property_stock_customer.id,
                'invoice_state': '2binvoiced',
            }
            move_id = move_obj.create(cr, uid, values)
            move_obj.action_assign(cr, uid, move_id, context=context)
            move_obj.action_done(cr, uid, move_id, context=context)
        self.write(cr, uid, ids, {'state': 'sale', 'sale_move_id': move_id})


    def _prepare_deposit_move(self, cr, uid, deposit, picking_id, group_id, context=None):

        product_uom = self.pool.get('product.uom')
        #price_unit = order_line.price_unit
        #if order_line.product_uom.id != order_line.product_id.uom_id.id:
        #    price_unit *= order_line.product_uom.factor
        #if order.currency_id.id != order.company_id.currency_id.id:

        #    price_unit = self.pool.get('res.currency').compute(cr, uid, order.currency_id.id, order.company_id.currency_id.id, price_unit, round=False, context=context)
        mod_obj = self.pool.get('ir.model.data')
        deposit_id = mod_obj.get_object_reference(cr, uid, 'stock_deposit', 'stock_location_deposit')
        picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
        res = []
        move_template = {
            'name': 'RET' or '',
            'product_id': deposit.product_id.id,
            'product_uom': deposit.product_uom.id,
            'product_uom_qty': deposit.product_uom_qty,
            'product_uos': deposit.product_uom.id,
            'location_id': deposit_id[1],
            'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
            'picking_id': picking_id,
            'partner_id': deposit.partner_id.id ,
            'move_dest_id': False,
            'state': 'draft',
            'company_id': deposit.company_id.id,

            'group_id': group_id,
            'procurement_id': False,
            'origin': False,
            'route_ids': picking.picking_type_id.warehouse_id and [(6, 0, [x.id for x in picking.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id':picking.picking_type_id.warehouse_id.id,
            'invoice_state': 'none'
        }
        res.append(move_template)
        return res

    def _create_stock_moves(self, cr, uid, deposit, picking_id=False, context=None):

        stock_move = self.pool.get('stock.move')
        todo_moves = []
        new_group = self.pool.get("procurement.group").create(cr, uid, {'name': 'deposit RET', 'partner_id': deposit.partner_id.id}, context=context)
        for vals in self._prepare_deposit_move(cr, uid, deposit, picking_id, new_group, context=context):
            move = stock_move.create(cr, uid, vals, context=context)
            todo_moves.append(move)

        todo_moves = stock_move.action_confirm(cr, uid, todo_moves)
        stock_move.force_assign(cr, uid, todo_moves)



    def return_deposit(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        picking_type_id = mod_obj.get_object_reference(cr, uid, 'stock', 'picking_type_in')
        for deposit in self.browse(cr, uid, ids):
            picking_id = self.pool.get('stock.picking').create(cr, uid, {'picking_type_id': picking_type_id[1], 'partner_id': deposit.partner_id.id}, context=context)
            self._create_stock_moves(cr, uid, deposit, picking_id, context=context)
        self.write(cr, uid, ids, {'state': 'returned', 'return_picking_id': picking_id})
