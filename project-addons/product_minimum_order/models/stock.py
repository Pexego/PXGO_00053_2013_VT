from odoo import models, api, _


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def action_copy_reserv_qty(self):
        super().action_copy_reserv_qty()
        for pick in self:
            stock_loc = self.env.ref('stock.stock_location_stock')
            for move in pick.move_lines:
                if move.reserved_availability % move.product_id.sale_in_groups_of != 0\
                        and (move.sale_line_id and not move.sale_line_id.product_id.is_pack)\
                        and move.location_id == stock_loc:
                    min_qty = move.product_id.sale_in_groups_of
                    # Assign the maximum qty available base on the minimum qty required
                    move.qty_confirmed = min_qty * (int(move.reserved_availability / min_qty))

    @api.multi
    def action_accept_confirmed_qty(self):
        for pick in self:
            stock_loc = self.env.ref('stock.stock_location_stock')
            for move in pick.move_lines:
                if move.qty_confirmed % move.product_id.sale_in_groups_of != 0\
                        and (move.sale_line_id and not move.sale_line_id.product_id.is_pack)\
                        and move.location_id == stock_loc:
                    min_qty = move.product_id.sale_in_groups_of
                    # Assign the maximum qty available base on the minimum qty required
                    move.qty_confirmed = min_qty * (int(move.qty_confirmed / min_qty))
        return super().action_accept_confirmed_qty()
