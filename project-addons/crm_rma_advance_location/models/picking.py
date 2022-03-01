from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    origin_move_id = fields.Many2one(
        comodel_name='stock.move',
        copy=False)

    child_move_ids = fields.One2many('stock.move', 'origin_move_id')

    @api.multi
    def _compute_qty_used(self):
        for move in self:
            move.qty_used = sum(move.child_move_ids.filtered(lambda m: m.state != 'cancel').mapped('product_uom_qty'))

    qty_used = fields.Float(compute="_compute_qty_used")
