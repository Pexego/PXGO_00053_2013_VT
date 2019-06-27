# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockMove(models.Model):

    _inherit = "stock.move"
    _order = 'has_reservations, picking_id, sequence, id'

    reservation_ids = fields.One2many("stock.reservation", "move_id",
                                      "Reservations", readonly=True)
    has_reservations = fields.Boolean(compute='_compute_has_reservations',
                                      store=True)

    @api.depends('reservation_ids')
    def _compute_has_reservations(self):
        for move in self:
            move.has_reservations = any(move.reservation_ids)

    def _assign_picking(self):
        no_pick_moves = self.\
            filtered(lambda x: x.location_dest_id.id == self.env.
                     ref('stock_reserve.stock_location_reservation').id)
        return super(StockMove, self - no_pick_moves)._assign_picking()
