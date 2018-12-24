from odoo import models

#TODO: Migrar
# ~ class procurement_order(orm.Model):

    # ~ _inherit = "procurement.order"

    # ~ _columns = {
        # ~ 'reservation_paused': fields.boolean('Reservation paused')
    # ~ }


class stock_move(models.Model):

    _inherit = "stock.move"

    def action_assign(self, cr, uid, ids, context=None):
        valid_ids = []
        res = False
        for move in self.browse(cr, uid, ids, context=context):
            if not move.procurement_id or not move.procurement_id.reservation_paused:
                valid_ids.append(move.id)

        if valid_ids:
            res = super(stock_move, self).action_assign(cr, uid, valid_ids, context=context)
        return res

