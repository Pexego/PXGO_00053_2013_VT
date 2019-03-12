# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_confirm(self):
        """
        When confirm a purchase order, if purchase order was created from a
        pre order, we try to find under minimum alerts with the same pre orders
        (That means really that purchase was created from a under minimum) in
        'In purchase' state and we finish it
        """
        res = super().button_confirm()
        under_min = self.env['product.stock.unsafety']
        for po in self:
            domain = [
                ('state', '=', 'in_action'),
                ('purchase_id', '=', po.id)
            ]
            under_min_objs = under_min.search(domain)
            if under_min_objs:
                under_min_objs.write({'state': 'finalized'})
        return res

    @api.multi
    def unlink(self):
        for order in self:
            under_mins = self.env['product.stock.unsafety'].search(
                [('purchase_id', '=', order.id)])
            if under_mins:
                under_mins.write({"state": "in_progress",
                                  "purchase_id": False})
        return super().unlink()


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    @api.multi
    def unlink(self):
        for line in self:
            under_mins = self.env['product.stock.unsafety'].search(
                [('purchase_id', '=', line.order_id.id),
                 ('product_id', '=', line.product_id.id)])
            if under_mins:
                under_mins.write({"state": "in_progress",
                                  "purchase_id": False})
        return super().unlink()
