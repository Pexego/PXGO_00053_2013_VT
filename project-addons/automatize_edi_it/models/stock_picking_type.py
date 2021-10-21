# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    force_location = fields.\
        Boolean("Force location",
                help="Force orig. location on picking creation")


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def _process_picking(self):
        for pick in self:
            pick.not_sync = True
            pick.action_assign()
            for move in pick.move_lines.filtered(lambda m: m.state not in
                                                 ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
            pick.action_done()


class StockMove(models.Model):

    _inherit = "stock.move"

    @api.multi
    def _action_done(self):
        res = super()._action_done()
        vendor_deposit_loc = self.env.ref("automatize_edi_it.stock_location_vendor_deposit")
        for move in self:
            if move.location_dest_id == vendor_deposit_loc:
                domain = [('state', 'in', ['confirmed',
                                           'partially_available']),
                          ('picking_type_code', '=', 'incoming'),
                          ('product_id', '=', move.product_id.id)]
                confirmed_ids = self.\
                    search(domain, limit=None,
                           order="has_reservations,date_expected,sequence,id")
                if confirmed_ids:
                    confirmed_ids._action_assign()
        return res

