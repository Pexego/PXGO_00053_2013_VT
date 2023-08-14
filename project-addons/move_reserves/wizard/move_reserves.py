from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class MoveReserves(models.TransientModel):
    _name = "move.reserves"

    product_id = fields.Many2one("product.product", "Product")
    qty = fields.Integer("Quantity")

    reserves_origin_id = fields.Many2one("stock.move")
    reserves_dest_id = fields.Many2one("stock.move")

    @api.onchange('product_id', 'qty')
    def on_change_product_id_origin(self):
        """Changes the domain of the reserves_origin_id field"""
        if self.product_id:
            self.reserves_origin_id = None
            return {'domain': {'reserves_origin_id': [('product_id', '=', self.product_id.id),
                                                      ('picking_type_id.code', '=', 'outgoing'),
                                                      ('state', 'not in', ['done', 'draft', 'cancel'])]}}

    @api.onchange('product_id', 'qty')
    def on_change_product_id_dest(self):
        """Changes the domain of the reserves_dest_id field"""
        if self.product_id:
            self.reserves_dest_id = None
            return {'domain': {'reserves_dest_id': [('product_id', '=', self.product_id.id),
                                                    ('state', 'not in', ['done', 'draft', 'cancel', 'assigned'])]}}

    def create_dummy_reserve(self, product, qty):
        """Creates a dummy reserve that serves as an intermediate"""
        now = datetime.now()
        date_validity = (now + relativedelta(days=1)).strftime("%Y-%m-%d")
        warehouse = self.env['stock.warehouse'].browse(1)
        vals = {
            'product_id': product.id,
            'product_uom': 1,
            'product_uom_qty': qty,
            'date_validity': date_validity,
            'name': product.name,
            'location_id': warehouse.lot_stock_id.id,
            'user_id': self.env.user.id
        }
        new_reservation = self.env['stock.reservation'].create(vals)
        return new_reservation

    def action_move_reserve(self):
        """
        Move reserves from one move to another
        Process:
            1. create reserve intermediate
            2. release origin
            3. reserve intermediate
            4. reserve origin
            5. release intermediate
            6. reserve destination
            7. delete intermediate
        """
        if self.reserves_origin_id.id == self.reserves_dest_id.id:
            raise UserError(_('You have selected the same move in both'))
        if self.qty > self.reserves_origin_id.reserved_availability:
            raise UserError(_('You have selected more quantity than is available in the origin reserve'))
        if self.qty > self.reserves_dest_id.product_uom_qty:
            raise UserError(_('You have selected more quantity than is in the destination reserve'))
        if self.qty == 0:
            raise UserError(_('You must select some quantity'))

        # 1. create reserve intermediate
        dummy_reserve = self.create_dummy_reserve(self.product_id, self.qty)
        # origin_qty_reserved = self.reserves_origin_id.reserved_availability
        sale_lines = None

        try:
            # 2. release origin
            if not self.reserves_origin_id.reservation_ids:
                # When is reserved directly on the picking there is not stock.reservation
                self.reserves_origin_id.action_do_unreserve()
            else:
                if self.reserves_origin_id.reservation_ids.mapped('sale_line_id'):
                    sale_lines = self.reserves_origin_id.reservation_ids.mapped('sale_line_id')
                self.reserves_origin_id.reservation_ids.release()  # TODO: sudo??

            # 3. reserve intermediate
            dummy_reserve.reserve()

            # 4. reserve origin
            if not self.reserves_origin_id.reservation_ids:
                # When is reserved directly on the picking there is not stock.reservation
                self.reserves_origin_id._action_assign()
            else:
                if sale_lines:
                    # if there were reserves but there was deleted
                    sale_lines.acquire_stock_reservation(date_validity=self.reserves_origin_id.reservation_ids[0].date_validity, note=None)
                    self.reserves_origin_id.reservation_ids.unlink()
                else:
                    self.reserves_origin_id.reservation_ids.reserve()

            # 5. release intermediate
            dummy_reserve.release()

            # 6. reserve destination
            self.reserves_dest_id._action_assign()

            # 7. delete intermediate
            dummy_reserve.unlink()

            # LOG
            self.env['reserves.log'].create({'user_id': self.env.user.id,
                                             'product_id': self.product_id.id,
                                             'qty': self.qty,
                                             'move': f'{self.reserves_origin_id.get_move_order_name()} -> {self.reserves_dest_id.get_move_order_name()}',
                                             'date': datetime.now()})

        except:
            raise UserError(_('There is been an error, try again later'))

class ReservesLog(models.TransientModel):
    _name = "reserves.log"
    _transient_max_hours = 744  # one month
    _transient_max_count = False

    user_id = fields.Many2one("res.users", "User")
    product_id = fields.Many2one("product.product", "Product")
    qty = fields.Integer("Quantity")
    move = fields.Char("Move")
    date = fields.Datetime("Date")
