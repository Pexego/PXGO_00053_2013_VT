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
