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

from openerp import models, fields, api, _, exceptions
from datetime import date

import ipdb

class StockContainer(models.Model):

    _name = "stock.container"

    @api.one
    @api.depends('move_ids')
    def _get_date_expected(self):
        min_date = False
        if self.move_ids:
            for move in self.move_ids:
                if move.picking_id:
                    if not min_date or min_date > move.picking_id.min_date:
                        min_date = move.picking_id.min_date
            if min_date:
                self.date_expected = min_date

        if not self.date_expected:
            self.date_expected = date.today()

    @api.one
    @api.depends('move_ids')
    def _get_picking_ids(self):
        res = []
        for line in self.move_ids:
            if line.picking_id.id not in res:
                res.append(line.picking_id.id)

        self.picking_ids = res

    name = fields.Char("Container Ref.", required=True)
    date_expected = fields.Date("Date expected", compute='_get_date_expected', readonly=True, required=False)
    move_ids = fields.One2many("stock.move", "container_id", "Moves",
                               readonly=True, copy=False)
    picking_ids = fields.One2many('stock.picking', compute='_get_picking_ids', string='Pickings', readonly=True)

    user_id = fields.Many2one('Responsible', compute='_get_responsible')
    company_id = fields.\
        Many2one("res.company", "Company", required=True,
                 default=lambda self:
                 self.env['res.company'].
                 _company_default_get('stock.container'))

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Container name must be unique')
    ]

    @api.one
    def _get_responsible(self):
        responsible = ''
        if self.picking_id:
            responsible = self.picking_id.commercial
        elif self.origin:
            responsible = self.env['sale.order'].search([('name', '=', self.origin)]).user_id
        return responsible

class stock_picking(models.Model):

    _inherit = 'stock.picking'

    shipping_identifier = fields.Char('Shipping identifier', size=64)
    temp = fields.Boolean("Temp.")

    @api.multi
    def action_cancel(self):
        for pick in self:
            if pick.temp:
                for move in pick.move_lines:
                    if move.state == "assigned":
                        move.do_unreserve()
                    move.state = "draft"
                    move.picking_id = False
        return super(stock_picking, self).action_cancel()


class stock_move(models.Model):

    _inherit = 'stock.move'

    partner_id = fields.Many2one('res.partner', 'Partner')
    container_id = fields.Many2one('stock.container', "Container")
    subtotal_price = fields.Float('Subtotal', compute='_calc_subtotal')
    partner_ref = fields.Char(related='purchase_line_id.order_id.partner_ref')

    @api.multi
    def _calc_subtotal(self):
        for move in self:
            move.subtotal_price = move.price_unit * move.product_uom_qty

    @api.multi
    def write(self, vals):
        res = super(stock_move, self).write(vals)
        for move in self:
            move.refresh()
            if move.picking_type_id.code == 'incoming':
                if vals.get('date_expected', False):
                    self.env['stock.reservation'].\
                        reassign_reservation_dates(move.product_id)
            if vals.get('state', False) == 'assigned':
                reserv_ids = self.env["stock.reservation"].\
                    search([('move_id', '=', move.id),
                            ('sale_line_id', '!=', False)])
                if reserv_ids:
                    notify = True
                    for line in reserv_ids[0].sale_line_id.\
                            order_id.order_line:
                        if line.id != reserv_ids[0].sale_line_id.id:
                            for reserv in line.reservation_ids:
                                if reserv.state != 'assigned':
                                    notify = False
                    if notify:
                        sale = reserv_ids[0].sale_line_id.order_id
                        followers = sale.message_follower_ids
                        sale.message_post(body=_("The sale order is already assigned."),
                                          subtype='mt_comment',
                                          partner_ids=followers)
            if vals.get('container_id', False):
                container = self.env["stock.container"].\
                    browse(vals['container_id'])
                move.date_expected = container.date_expected
        return res

    @api.model
    def create(self, vals):
        res = super(stock_move, self).create(vals)
        if (vals.get('picking_type_id', False) and
                res.picking_type_id.code == 'incoming'):
            if 'date_expected' in vals.keys():
                self.env['stock.reservation'].\
                    reassign_reservation_dates(res.product_id)
        if not res.partner_id and res.picking_id.partner_id == \
                self.env.ref('purchase_picking.partner_multisupplier'):
            raise exceptions.Warning(
                _('Partner error'), _('Set the partner in the created moves'))
        return res

    def _get_master_data(self, cr, uid, move, company, context=None):
        partner, uid, currency = super(stock_move, self)._get_master_data(
            cr, uid, move, company, context)
        if move.picking_type_code == "incoming":
            if move.partner_id:
                partner = move.partner_id
            else:
                partner = move.picking_id.partner_id
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
