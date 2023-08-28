from odoo import models, api


class StockMove(models.Model):
    _inherit = "stock.move"

    def get_move_order_name(self):
        return (self.sale_line_id.order_id.display_name or self.purchase_line_id.order_id.display_name
                or self.raw_material_production_id.display_name or self.production_id.display_name or self.picking_id.name)

    @api.multi
    def name_get(self):
        result = []
        for move in self.filtered(lambda m: m.picking_type_id.code == 'outgoing' and m.state not in ['done', 'draft', 'cancel']):
            if move.picking_id:
                name = f"{int(move.reserved_availability) or '_'} uds | {move.origin or move.get_move_order_name() or '_'} | {move.picking_id.name or '_'} | {move.user_id.name or '_'}"
            else:
                name = f"{int(move.reserved_availability) or '_'} uds | {move.origin or move.get_move_order_name() or '_'} | {move.user_id.name or '_'}"
            result.append((move.id, name))
        res = super(StockMove, self.filtered(lambda m: m.picking_type_id.code != 'outgoing' or m.state in ['done', 'draft', 'cancel'])).name_get()
        return result + res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        domain = []
        if name:
            domain = ['|', ('reference', operator, name), ('origin', operator, name)]
        return self.search(args + domain, limit=limit).name_get()

