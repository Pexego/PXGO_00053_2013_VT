# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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

from openerp import models, api, _, fields


class StockLotacion(models.Model):

    _inherit = 'stock.location'

    def move_pantry_kitchen(self, product_id, qty):
        self.location_move(product_id, 'stock_location_pantry', qty,
                           'stock_location_kitchen')

    def move_kitchen_cooked(self, product_id, qty):
        self.location_move(product_id, 'stock_location_kitchen', qty,
                           'stock.stock_location_stock', True)

    def move_kitchen_nursing(self, product_id, qty):
        self.location_move(product_id, 'stock_location_kitchen', qty,
                           'stock_location_nursing')

    def move_nursing_damaged(self, product_id, qty):
        self.location_move(product_id, 'stock_location_nursing', qty,
                           'stock_location_damaged')

    def move_nursing_cooked(self, product_id, qty):
        self.location_move(product_id, 'stock_location_nursing', qty,
                           'stock.stock_location_stock', True)

    def move_quality_cooked(self, product_id, qty):
        self.location_move(product_id, 'stock_location_quality', qty,
                           'stock.stock_location_stock', True)

    def move_cooked_nursing(self, product_id, qty):
        self.location_move(product_id, 'stock.stock_location_stock', qty,
                           'stock_location_nursing')

    def move_cooked_damaged(self, product_id, qty):
        self.location_move(product_id, 'stock.stock_location_stock', qty,
                           'stock_location_damaged')

    def location_move(self, product_id, source_location, qty, dest_location,
                      send_message=False):
        product = self.env['product.product'].browse(product_id)
        source_location = '.' in source_location and \
            source_location or 'location_moves.' + source_location
        dest_location = '.' in dest_location and \
            dest_location or 'location_moves.' + dest_location
        source_location = self.env.ref(source_location)
        dest_location = self.env.ref(dest_location)
        type_id = self.env['stock.picking.type'].search([('code', '=',
                                                          'internal')])
        pick_vals = {
            'partner_id': self.env.user.company_id.partner_id.id,
            'picking_type_id': type_id.id,
        }
        picking = self.env['stock.picking'].create(pick_vals)
        move_template = {
            'name': product.name,
            'product_id': product.id,
            'picking_type_id': type_id.id,
            'product_uom': product.uom_id.id,
            'product_uos': product.uom_id.id,
            'product_uom_qty': qty,
            'product_uos_qty': qty,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'picking_id': picking.id,
            'partner_id': picking.partner_id.id,
            'move_dest_id': False,
            'state': 'draft',
            'company_id': self.env.user.company_id.id,
            'invoice_state': 'none',
        }
        new_move = self.env['stock.move'].create(move_template)
        if send_message:
            self.reassign_reservation_dates(product, [new_move])
        picking.action_assign()
        picking.action_done()

    @api.model
    def reassign_reservation_dates(self, product_id, moves):
        uom_obj = self.env['product.uom']
        product_uom = product_id.uom_id
        reservations = self.env['stock.reservation'].search(
            [('product_id', '=', product_id.id),
             ('state', '=', 'confirmed')])
        reservation_index = 0

        reservation_used = 0
        for move in moves:
            qty_used = 0
            product_uom_qty = uom_obj._compute_qty_obj(
                move.product_uom, move.product_uom_qty, product_uom)
            while qty_used < product_uom_qty and reservation_index < \
                    len(reservations):
                reservation = reservations[reservation_index]
                reservation_qty = reservation.product_uom_qty - \
                    reservation.reserved_availability
                reservation_qty = uom_obj._compute_qty_obj(
                    reservation.product_uom, reservation_qty, product_uom)
                if reservation_qty - reservation_used <= product_uom_qty - \
                        qty_used:
                    reservation.date_planned = move.date_expected
                    reservation_index += 1
                    if reservation.sale_id:
                        sale = reservation.sale_id
                        followers = sale.message_follower_ids
                        sale.message_post(
                            body=_("The date planned of the reservation was \
                                   changed."),
                            subtype='mt_comment', partner_ids=followers)
                else:
                    reservation_used += product_uom_qty - qty_used
                    break
                qty_used += reservation_qty - reservation_used
                reservation_used = 0
        while reservation_index < len(reservations):
            reservations[reservation_index].date_planned = False
            reservation_index += 1


class StockMove(models.Model):

    _inherit = "stock.move"

    location_usage = fields.Selection([('supplier', 'Supplier Location'),
                                       ('view', 'View'),
                                       ('internal', 'Internal Location'),
                                       ('customer', 'Customer Location'),
                                       ('inventory', 'Inventory'),
                                       ('procurement', 'Procurement'),
                                       ('production', 'Production'),
                                       ('transit', 'Transit Location')],
                                      related="location_id.usage",
                                      readonly=True)
    picking_type_code = fields.Selection([('incoming', 'Suppliers'),
                                          ('outgoing', 'Customers'),
                                          ('internal', 'Internal')],
                                         related="picking_type_id.code",
                                         readonly=True)

    @api.multi
    def unit_to_quality(self):
        wzd_obj = self.env["quality.move.wzd"]
        for move in self:
            wzd = wzd_obj.create({'qty': 1.0})
            wzd.with_context(active_id=move.id).action_move()
        return True
