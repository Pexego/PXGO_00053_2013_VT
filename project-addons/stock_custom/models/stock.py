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
from odoo import api, exceptions, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = "priority desc, date desc, id desc"

    internal_notes = fields.Text()
    commercial = fields.Many2one('res.users')

    def action_done(self):
        lot_obj = self.env["stock.production.lot"]
        for picking in self:
            for move_line in picking.move_line_ids:
                if move_line.lots_text:
                    txlots = move_line.lots_text.split(',')
                    if len(txlots) != move_line.qty_done:
                        raise exceptions.Warning(_("The number of lots defined"
                                                   " are not equal to move"
                                                   " product quantity"))
                    while (txlots):
                        lot_name = txlots.pop()
                        lot = lot_obj.search([("name", "=", lot_name),
                                              ("product_id", "=",
                                               move_line.product_id.id)],
                                             limit=1)
                        if not lot:
                            lot = lot_obj.create({'name': lot_name,
                                                  'product_id':
                                                  move_line.product_id.id})
                        if move_line.qty_done > 1:
                            move_line.qty_done = move_line.qty_done - 1
                            move_line.copy({'qty_done': 1, 'lot_id': lot.id})
                        else:
                            move_line.lot_id = lot
        res = super().action_done()
        for picking in self:
            if picking.state == 'done' and picking.sale_id and \
                    picking.picking_type_code == 'outgoing':
                picking_template = self.env.\
                    ref('stock_custom.picking_done_template')
                picking_template.with_context(
                    lang=picking.partner_id.lang).send_mail(picking.id)
        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    lots_text = fields.Text('Lots', help="Value must be separated by commas")


class StockMove(models.Model):
    _inherit = "stock.move"

    _order = 'date_expected asc, id'

    real_stock = fields.Float(compute='_compute_real_stock')
    available_stock = fields.Float(compute="_compute_available_stock")
    user_id = fields.Many2one('res.users', compute='_compute_responsible')

    def _compute_responsible(self):
        for move in self:
            responsible = None
            if move.picking_id:
                responsible = move.picking_id.commercial.id
            elif move.origin:
                responsible = move.env['sale.order'].search(
                    [('name', '=', move.origin)]).user_id.id
            move.user_id = responsible

    def _compute_available_stock(self):
        for move in self:
            move.available_stock = move.product_id.virtual_stock_conservative

    def _compute_real_stock(self):
        for move in self:
            move.real_stock = move.product_id.qty_available

    @api.multi
    def _action_done(self):
        res = super()._action_done()
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
                    confirmed_ids._action_assign()

        return res


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        new_picking, pick_type_id = super()._create_returns()
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

    next_reception_date = fields.Date(compute='_compute_next_reception_date')

    def _compute_next_reception_date(self):
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


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        compute='_compute_partner_id',
        help='The last customer in possession of the product')
    lot_notes = fields.Text('Notes')

    def _compute_partner_id(self):
        pass
        for lot in self:
            move_line = self.env['stock.move.line'].search(
                [('lot_id', '=', lot.id)], order="id desc", limit=1)
            if move_line:
                lot.partner_id = \
                    move_line.picking_id.partner_id.commercial_partner_id
            else:
                lot.partner_id = False
