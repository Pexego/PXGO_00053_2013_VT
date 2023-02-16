from odoo import models

class SaleOrder(models.Model):

    _inherit = 'sale.order'

    def filter_lines_to_reserve(self):
        res = super(SaleOrder, self).filter_lines_to_reserve()
        route_order_id = self.env.ref('stock_dropshipping.route_drop_shipping').id
        return res.filtered(lambda l: not l.route_id or l.route_id.id!=route_order_id)

