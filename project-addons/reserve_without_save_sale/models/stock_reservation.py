# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, registry, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class StockReservation(models.Model):

    _name = 'stock.reservation'
    _inherit = ['stock.reservation', 'mail.thread']
    _order = "sequence asc"

    def _new_sequence(self):
        query = "SELECT MAX(sequence)  FROM stock_reservation "
        self.env.cr.execute(query, ())
        regs = self.env.cr.fetchall()
        for reg in regs:
            if not reg[0]:
                seq = 0
            else:
                seq = reg[0]
            sequence = seq + 1
        return sequence

    unique_js_id = fields.Char(size=64)
    sequence = fields.Integer(help='Gives the priority in reservation.',
                              default=_new_sequence)
    user_id = fields.Many2one('res.users', relation='sale_id.user_id',
                              string='Responsible', readonly=True)
    date_order = fields.Datetime(relation='sale_id.date_order', readonly=True)
    partner_id = fields.Many2one('res.partner', relation='sale_id.partner_id',
                                 readonly=True)

    @api.model
    def create(self, vals):
        context2 = dict(self._context)
        context2.pop('default_state', False)
        res = super(StockReservation, self.with_context(context2)).create(vals)
        if vals.get('unique_js_id', False) and \
                not vals.get('sale_line_id', False):
            with registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid,
                                          self.env.context)

                new_env.cr.execute("select id from sale_order_line where "
                                   "unique_js_id = '%s'" % vals['unique_js_id']
                                   )

                lines = new_env.cr.fetchone()
                if lines:
                    self.with_env(new_env).write({'sale_line_id': lines[0]})
                new_env.cr.commit()
        return res

    def write(self, vals):
        if vals.get('sequence', False) and self._context.get('first', False):
            old_sequences = {}
            for reservation in self:
                old_sequences[reservation.id] = reservation.sequence
            res = super().write(vals)
            self.with_context(sequences=old_sequences).reassign()
        else:
            res = super().write(vals)
        return res

    def reassign(self):
        for reservation in self:
            old_sequence = self._context.get('sequences', False)
            if old_sequence:
                sequence = min(
                    old_sequence[reservation.id], reservation.sequence)
            else:
                sequence = reservation.sequence
            reserv_ids = self.search(
                [('sequence', '>=', sequence),
                 ('product_id', '=', reservation.product_id.id),
                 ('state', 'in', ['draft', 'confirmed', 'assigned'])])
        # Undo all reserves in reservations under the first sequence
        reserv_ids.do_complete_release()
        reserv_ids.reserve()
        return True

    def do_complete_release(self):
        for reserve in self:
            if reserve.state in ('done', 'cancel'):
                raise UserError(
                    _('Cannot unreserve a done reserve'))
            reserve.move_id._do_unreserve()
            reserve.write({'state': 'draft'})
            reserve.refresh()

    def reserve(self):
        """ Confirm a reservation
        The reservation is done using the default UOM of the product.
        A date until which the product is reserved can be specified.
        """
        current_sale_line_id = self.sale_line_id.id
        self.refresh()
        res = super().reserve()
        self.refresh()
        for move in res:
            reservation = self.env['stock.reservation'].search(
                [('move_id', '=', move.id)])
            if not reservation:
                reservation = self.env['stock.reservation'].create(
                    {'move_id': move.id, 'sale_line_id': current_sale_line_id})
            reservation.message_post(
                body=_("Reserva modificada. Estado '%s'") % reservation.state)
        return res

    def release(self):
        res = super().release()
        for reserve in self:
            reserve.message_post(body=_("Reserva liberada."))
        return res

    @api.model
    def delete_orphan_reserves(self):
        # TODO: pendiente de migrar sale_product_customize
        now = fields.Datetime.now()
        d = datetime.strptime(now, '%Y-%m-%d %H:%M:%S') + \
            timedelta(minutes=-30)
        last_date = datetime.strftime(d, '%Y-%m-%d %H:%M:%S')
        reserves = self.search([('create_date', '<=', last_date),
                                ('sale_line_id', '=', False),
                                ('mrp_id', '=', False),
                                ('claim_id', '=', False),
                                ('move_id.state', 'not in', ['done',
                                                             'cancel'])])

        if reserves:
            reserves.unlink()

        reserves_loc = self.env.ref("stock_reserve.stock_location_reservation")
        moves = self.env["stock.move"].search([('location_dest_id', '=',
                                                reserves_loc.id),
                                               ('state', '!=', "cancel"),
                                               ('reservation_ids', '=',
                                                False)])
        if moves:
            moves.action_cancel()

        return True
