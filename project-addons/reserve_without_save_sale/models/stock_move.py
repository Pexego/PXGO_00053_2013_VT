# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockMove(models.Model):

    _inherit = "stock.move"
    _order = 'has_reservations, sequence, picking_id, id'

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

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.context.get('reverse_order'):
            order = \
                'has_reservations,sequence desc,picking_id desc,id desc'
        return super().search(args, offset=offset, limit=limit, order=order,
                              count=count)


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _run_scheduler_tasks(self, use_new_cursor=False, company_id=False):
        super(ProcurementGroup, self.with_context(reverse_order=True)).\
            _run_scheduler_tasks(use_new_cursor=use_new_cursor,
                                 company_id=company_id)
