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
from openerp import models, fields, exceptions, api, _ipdb


class StockHistory(models.Model):
    _inherit = 'stock.history'

    brand_id = fields.Many2one(string="Brand", related='move_id.product_id.product_brand_id')


class stock_picking(models.Model):
    _inherit = "stock.picking"
    _order = "priority desc, date desc, id desc"

    internal_notes = fields.Text("Internal Notes")
    commercial = fields.Many2one('res.users')

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

        res =  super(stock_picking, self).action_done()
        for picking in self:
            if picking.state == 'done' and picking.sale_id and \
                    picking.picking_type_code == 'outgoing':
                picking_template = self.env.\
                    ref('stock_custom.picking_done_template')
                picking_template.with_context(
                    lang=picking.partner_id.lang).send_mail(picking.id)
        return res


class stock_move(models.Model):
    _inherit = "stock.move"

    _order = 'date_expected asc, id'

    lots_text = fields.Text('Lots', help="Value must be separated by commas")
    real_stock = fields.Float('Real Stock', compute='_get_real_stock')
    available_stock = fields.Float('Available Stock', compute="_get_available_stock")
    user_id = fields.Many2one('res.users', compute='_get_responsible')

    @api.one
    def _get_responsible(self):
        responsible = None
        if self.picking_id:
            responsible = self.picking_id.commercial.id
        elif self.origin:
            responsible = self.env['sale.order'].search([('name', '=', self.origin)]).user_id.id
        self.user_id = responsible

    @api.one
    def _get_available_stock(self):
        self.available_stock = self.product_id.virtual_stock_conservative

    @api.one
    def _get_real_stock(self):
        self.real_stock = self.product_id.qty_available

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
                              '|', ('picking_type_code', '=', 'outgoing'),
                              ('id', 'in', reserve_move_ids)]

                confirmed_ids = self.\
                    search(domain, limit=None)
                if confirmed_ids:
                    confirmed_ids.action_assign()

        return res


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        new_picking, pick_type_id = super(StockReturnPicking, self).\
            _create_returns()
        pick_type_obj = self.env["stock.picking.type"].browse(pick_type_id)
        if pick_type_obj.code == "incoming":
            pick_obj = self.env["stock.picking"].browse(new_picking)
            for move in pick_obj.move_lines:
                if move.warehouse_id.lot_stock_id == move.location_dest_id:
                    move.location_dest_id = \
                        move.warehouse_id.wh_input_stock_loc_id.id

        return new_picking, pick_type_id


class StockReservation(models.Model):
    _inherit = 'stock.reservation'

    next_reception_date = fields.Date('Next reception date',
                                      compute='_get_next_reception')

    @api.multi
    def _get_next_reception(self):
        for res in self:
            date_expected = False
            moves = self.env['stock.move'].search(
                [('state', 'in', ('waiting', 'confirmed', 'assigned')),
                 ('product_id', '=', res.product_id.id),
                 ('location_id', '=',
                  res.sale_id.warehouse_id.wh_input_stock_loc_id.id),
                 ('location_dest_id', 'child_of',
                  [res.sale_id.warehouse_id.view_location_id.id])],
                order='date_expected asc')
            if not moves:
                supp_id = self.env.ref('stock.stock_location_suppliers').id
                moves = self.env['stock.move'].search(
                    [('state', 'in', ('waiting', 'confirmed', 'assigned')),
                     ('product_id', '=', res.product_id.id),
                     ('location_id', '=', supp_id),
                     ('location_dest_id', 'child_of',
                      [res.sale_id.warehouse_id.view_location_id.id])],
                    order='date_expected asc')
            if moves:
                date_expected = moves[0].date_expected
            res.next_reception_date = date_expected
