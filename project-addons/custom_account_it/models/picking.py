from odoo import models, api
import numpy

class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        res = super().action_done()
        for picking in self:
            if picking.picking_type_id.code == "outgoing":
                for move in picking.move_lines:
                    if move.move_orig_ids:
                        cost = numpy.average(move.move_orig_ids.mapped('price_unit'))
                        move.price_unit =  cost * -1
                        move.invoice_line_ids.write({'cost_unit':cost})
        return res

