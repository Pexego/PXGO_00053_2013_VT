# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos
#    $Carlos Lombardía Rodríguez <carlos@comunitea.com>$
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
from openerp import models, fields, exceptions, api, _


class stock_picking(models.Model):
    _inherit = "stock.picking"

    internal_notes = fields.Text("Internal Notes")

    @api.multi
    def action_done(self):
        packop = self.env["stock.pack.operation"]
        lot_obj = self.env["stock.production.lot"]
        link_obj = self.env["stock.move.operation.link"]
        for pick in self:
            for move in pick.move_lines:
                if move.lots_text:
                    if move.linked_move_operation_ids:
                        move.linked_move_operation_ids.unlink()
                        move.refresh()
                    txlots = move.lots_text.split(',')
                    if len(txlots) != (move.qty_ready or move.product_uom_qty):
                        raise exceptions.Warning(_("The number of lots defined"
                                                   " are not equal to move"
                                                   " product quantity"))
                    while (txlots):
                        lot_name = txlots.pop()
                        lots = lot_obj.search([("name", "=", lot_name),
                                               ("product_id", "=",
                                                move.product_id.id)])
                        if lots:
                            lot = lots[0]
                        else:
                            lot = lot_obj.create({'name': lot_name,
                                                  'product_id':
                                                  move.product_id.id})
                        op = packop.with_context(no_recompute=True).\
                            create({'picking_id': move.picking_id.id,
                                    'product_id': move.product_id.id,
                                    'product_uom_id': move.product_uom.id,
                                    'product_qty': 1.0,
                                    'lot_id': lot.id,
                                    'location_id': move.location_id.id,
                                    'location_dest_id': move.
                                    location_dest_id.id
                                    })
                        link_obj.create({'qty': 1.0,
                                         'operation_id': op.id,
                                         'move_id': move.id})
                        move.refresh()

        return super(stock_picking, self).action_done()


class stock_move(models.Model):
    _inherit = "stock.move"

    lots_text = fields.Text('Lots', help="Value must be separated by commas")

    def _prepare_picking_assign(self, cr, uid, move, context=None):
        res = super(stock_move, self)._prepare_picking_assign(cr, uid, move,
                                                              context=context)
        res['internal_notes'] = (move.procurement_id and
                                 move.procurement_id.sale_line_id) and \
            move.procurement_id.sale_line_id.order_id.internal_notes or ""
        return res

    @api.multi
    def action_done(self):
        res = super(stock_move, self).action_done()
        stock_loc = self.env.ref("stock.stock_location_stock")
        for move in self:
            if move.location_dest_id == stock_loc:
                domain = [('state', '=', 'confirmed'),
                          ('picking_type_code', '=', 'outgoing'),
                          ('product_id', '=', move.product_id.id)]
                reserve_ids = self.env["stock.reservation"].\
                    search([('product_id', '=', move.product_id.id),
                            ('state', '=', 'confirmed'),
                            ('sale_line_id', '!=', False)])
                if reserve_ids:
                    reserve_move_ids = [x.move_id.id for x in reserve_ids]
                    domain = [('state', '=', 'confirmed'),
                              ('product_id', '=', move.product_id.id),
                              '|',('picking_type_code', '=', 'outgoing'),
                              ('id', 'in', reserve_move_ids)]

                confirmed_ids = self.\
                    search(domain, limit=None,
                           order='priority desc, date_expected asc')
                if confirmed_ids:
                    confirmed_ids.action_assign()

        return res
