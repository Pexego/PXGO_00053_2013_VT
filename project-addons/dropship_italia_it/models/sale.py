from odoo import models, api, fields


class SaleOrder(models.Model):

    _inherit = "sale.order"

    all_dropship = fields.Boolean("All Dropship")

    def action_confirm(self):
        res = super().action_confirm()
        purchase = self.env['purchase.order'].search([('origin', '=', self.name), ('state', '=', 'draft')])
        if purchase:
            if purchase.picking_type_id == self.env.ref('stock_dropshipping.picking_type_dropship'):
                purchase.confirm_and_create_order_es()
        return res

    def action_cancel(self):
        res = super().action_cancel()
        purchase = self.env['purchase.order'].search([('origin', '=', self.name), ('state', 'in', ('done', 'purchase'))])
        if purchase:
            purchase[0].sudo().button_cancel()
        return res

    @api.onchange('all_dropship')
    @api.multi
    def mark_all_dropship(self):
        for order in self:
            if order.all_dropship:
                for line in order.order_line:
                    line.route_id = self.env.ref('stock_dropshipping.route_drop_shipping')
            else:
                for line in order.order_line:
                    line.route_id = False
