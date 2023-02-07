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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        warehouse = self.env['stock.warehouse'].browse(self.env.context.get('warehouse_id'))
        loc_rma = warehouse.lot_rma_id
        for picking in self:
            if picking.location_dest_id == loc_rma and picking.claim_id:
                for move in picking.move_lines:
                    deposit = move.claim_line_id.deposit_id
                    if deposit and deposit.state == 'rma':
                        deposit.state = 'draft'
        return res

