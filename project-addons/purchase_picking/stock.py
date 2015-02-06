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


class stock_picking(models.Model):

    _inherit = 'stock.picking'

    shipping_identifier = fields.Char('Shipping identifier', size=64)

    @api.one
    def action_done(self):
        all_purchases = []
        res = super(stock_picking, self).action_done()
        for line in self.move_lines:
            if line.state == 'done' and line.purchase_line_id and line.purchase_line_id.order_id not in all_purchases:
                all_purchases.append(line.purchase_line_id.order_id)
        all_purchases = list(set(all_purchases))
        for purchase in all_purchases:
            followers = purchase.message_follower_ids
            purchase.message_post(body=_("Goods received."),
                                  subtype='mt_comment',
                                  partner_ids=followers)

        return res


class stock_move(models.Model):

    _inherit = 'stock.move'

    partner_id = fields.Many2one('res.partner', 'Partner')


    def _get_master_data(self, cr, uid, move, company, context=None):
        ''' returns a tuple (browse_record(res.partner), ID(res.users),
            ID(res.currency)'''
        return move.partner_id, uid, company.currency_id.id

    @api.one
    def write(self, vals):
        res = super (stock_move, self).write(vals)
        if self.picking_type_id.code == 'incoming':
            if 'date_expected' in vals.keys():
                self.env['stock.reservation'].reassign_reservation_dates(self.product_id)
        return res

    @api.model
    def create(self, vals):
        res = super(stock_move, self).create(vals)
        if 'picking_type_id' in vals.keys() and res.picking_type_id.code == 'incoming':
            if 'date_expected' in vals.keys():
                self.env['stock.reservation'].reassign_reservation_dates(res.product_id)
        return res


    def _get_master_data(self, cr, uid, move, company, context=None):
        partner, uid, currency = super(stock_move, self)._get_master_data(
            cr, uid, move, company, context)
        partner = move.partner_id
        return partner, uid, currency


class stock_reservation(models.Model):
    _inherit = 'stock.reservation'

    @api.model
    def reassign_reservation_dates(self, product_id):
        uom_obj = self.env['product.uom']
        product_uom = product_id.uom_id
        reservations = self.search(
            [('product_id', '=', product_id.id),
             ('state', '=', 'confirmed')])
        moves = self.env['stock.move'].search(
            [('product_id', '=', product_id.id),
             ('state', '=', 'draft'),
             ('picking_type_id.code', '=', u'incoming')],
             order='date_expected')
        reservation_index = 0

        reservation_used = 0
        for move in moves:
            qty_used = 0
            product_uom_qty = uom_obj._compute_qty_obj(move.product_uom, move.product_uom_qty, product_uom)
            while qty_used < product_uom_qty and reservation_index < len(reservations):
                reservation = reservations[reservation_index]
                reservation_qty = reservation.product_uom_qty - reservation.reserved_availability
                reservation_qty = uom_obj._compute_qty_obj(reservation.product_uom, reservation_qty, product_uom)
                if reservation_qty - reservation_used <= product_uom_qty - qty_used:
                    reservation.date_planned = move.date_expected
                    reservation_index += 1
                    if reservation.sale_id:
                        sale = reservation.sale_id
                        followers = sale.message_follower_ids
                        sale.message_post(body=_("The date planned of the reservation was changed."),
                                          subtype='mt_comment',
                                          partner_ids=followers)
                else:
                    reservation_used += product_uom_qty - qty_used
                    break
                qty_used += reservation_qty - reservation_used
                reservation_used = 0
        while reservation_index < len(reservations):
            reservations[reservation_index].date_planned = False
            reservation_index += 1

    @api.multi
    def reassign(self):
        context = dict(self.env.context)
        context.pop('first', False)
        res = super(stock_reservation, self).reassign()
        for reservation in self:
            self.with_context(context).reassign_reservation_dates(reservation.product_id)
        return res
