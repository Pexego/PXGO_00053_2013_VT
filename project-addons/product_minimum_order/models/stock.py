from odoo import models, api, _


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def action_copy_reserv_qty(self):
        super().action_copy_reserv_qty()
        for pick in self:
            for move in pick.move_lines:
                if move.reserved_availability % move.product_id.sale_in_groups_of != 0:
                    min_qty = move.product_id.sale_in_groups_of
                    # Assign the maximum qty available base on the minimum qty required
                    move.qty_confirmed = min_qty * (int(move.reserved_availability / min_qty))

    @api.multi
    def action_accept_confirmed_qty(self):
        for pick in self:
            for move in pick.move_lines:
                if move.qty_confirmed % move.product_id.sale_in_groups_of != 0:
                    min_qty = move.product_id.sale_in_groups_of
                    # Assign the maximum qty available base on the minimum qty required
                    move.qty_confirmed = min_qty * (int(move.qty_confirmed / min_qty))
        super().action_accept_confirmed_qty()
