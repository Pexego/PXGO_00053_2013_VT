# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockMove(models.Model):

    _inherit = "stock.move"
    _order = 'has_reservations, picking_id, sequence, id'

    reservation_ids = fields.One2many("stock.reservation", "move_id",
                                      "Reservations", readonly=True)
    has_reservations = fields.Boolean(compute='_compute_has_reservations', store=True)

    @api.depends('reservation_ids')
    def _compute_has_reservations(self):
        for move in self:
            move.has_reservations = any(move.reservation_ids)

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     objs = super().search(args, offset, limit, order, count)
    #     reserve_ids = self.env['stock.reservation'].search_read(
    #         [('move_id', 'in', objs._ids)], ['move_id'], order='sequence asc')
    #     ordered_ids = [x['move_id'][0] for x in reserve_ids]
    #     not_ordered_ids = [p for p in objs._ids if p not in ordered_ids]
    #     objs = not_ordered_ids + ordered_ids
    #     return objs
