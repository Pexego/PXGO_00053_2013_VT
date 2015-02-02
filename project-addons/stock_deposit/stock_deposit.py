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
from openerp import models, fields, api


class stock_deposit(models.Model):
    _name = 'stock.deposit'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    product_id = fields.Many2one(string='Product',
                                 related='move_id.product_id',
                                 store=True, readonly=True)
    product_uom_qty = fields.Float('Product qty',
                                   related='move_id.product_uom_qty',
                                   store=True, readonly=True)
    product_uom = fields.Many2one(related='move_id.product_uom',
                                  string='Uom',
                                  store=True,
                                  readonly=True)
    invoiced = fields.Boolean('Invoiced')
    move_id = fields.Many2one('stock.move', 'Deposit Move', required=True,
                              readonly=True, ondelete='cascade', select=1)
    picking_id = fields.Many2one(related='move_id.picking_id',
                                 string='Picking',
                                 store=True,
                                 readonly=True)
    partner_id = fields.Many2one(related='move_id.partner_id',
                                 string='Destination Address',
                                 store=True,
                                 readonly=True)
    sale_id = fields.Many2one(related='move_id.procurement_id.sale_line_id.order_id',
                              string='Sale',
                              store=True,
                              readonly=True)
    delivery_date = fields.Datetime('Date of Transfer')
    return_date = fields.Date('Return date')
    company_id = fields.Many2one(related='move_id.company_id',
                                 string='Date of Transfer',
                                 store=True,
                                 readonly=True)
    state = fields.Selection([('done', 'Done'), ('sale', 'Sale'),
                              ('returned', 'Returned')], 'State',
                             readonly=True, required=True)
    sale_move_id = fields.Many2one('stock.move', 'Sale Move', required=False,
                                   readonly=True, ondelete='cascade', select=1)
    return_picking_id = fields.Many2one('stock.picking', 'Return Picking',
                                        required=False, readonly=True,
                                        ondelete='cascade', select=1)
    user_id = fields.Many2one('res.users', 'Comercial', required=False,
                              readonly=True, ondelete='cascade', select=1)

    @api.multi
    def sale(self):
        move_obj = self.env['stock.move']
        for deposit in self:
            values = {
                'product_id': deposit.product_id.id,
                'product_uom_qty': deposit.product_uom_qty,
                'product_uom': deposit.product_uom.id,
                'partner_id': deposit.partner_id.id,
                'name': 'Sale Deposit: ' + deposit.move_id.name,
                'location_id': deposit.move_id.location_dest_id.id,
                'location_dest_id': deposit.partner_id.property_stock_customer.id,
                'invoice_state': 'none',
            }
            move = move_obj.create(values)
            move.action_assign()
            move.action_done()
            deposit.write({'state': 'sale', 'sale_move_id': move.id})

    @api.one
    def _prepare_deposit_move(self, picking, group):
        deposit_id = self.env.ref('stock_deposit.stock_location_deposit')
        res = []
        move_template = {
            'name': 'RET' or '',
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': self.product_uom_qty,
            'product_uos': self.product_uom.id,
            'location_id': deposit_id[1],
            'location_dest_id':
                picking.picking_type_id.default_location_dest_id.id,
            'picking_id': picking.id,
            'partner_id': self.partner_id.id,
            'move_dest_id': False,
            'state': 'draft',
            'company_id': self.company_id.id,
            'group_id': group.id,
            'procurement_id': False,
            'origin': False,
            'route_ids':
                picking.picking_type_id.warehouse_id and
                [(6, 0,
                  [x.id for x in
                   picking.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': picking.picking_type_id.warehouse_id.id,
            'invoice_state': 'none'
        }
        res.append(move_template)
        return res

    @api.one
    def _create_stock_moves(self, picking=False):
        stock_move = self.env['stock.move']
        todo_moves = self.env['stock.move']
        new_group = self.env['procurement.group'].create(
            {'name': 'deposit RET', 'partner_id': self.partner_id.id})
        for vals in self._prepare_deposit_move(picking, new_group):
            todo_moves += stock_move.create(vals)

        todo_moves = todo_moves.action_confirm()
        todo_moves.force_assign()

    @api.multi
    def return_deposit(self):
        picking_type_id = self.env.ref('stock.picking_type_in')
        for deposit in self:
            picking = self.env['stock.picking'].create(
                {'picking_type_id': picking_type_id[1],
                 'partner_id': deposit.partner_id.id})
            deposit._create_stock_moves(picking)
            deposit.write({'state': 'returned',
                           'return_picking_id': picking.id})
