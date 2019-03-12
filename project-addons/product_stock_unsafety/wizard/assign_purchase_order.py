# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, _


class AssignPurchaseOrderWzd(models.TransientModel):

    _name = "assign.purchase.order.wzd"

    purchase_id = fields.Many2one("purchase.order", "Purchase",
                                  domain=[('state', '=', 'draft')])

    def assign_purchase_order(self):
        self.ensure_one()
        for line in self.env["product.stock.unsafety"].browse(
                self.env.context['active_ids']):
            line.purchase_id = self.purchase_id
            line.state = "in_action"
            line.supplier_id = self.purchase_id.partner_id.id
            purchase = self.purchase_id
            line_vals = {'order_id': purchase.id,
                         'partner_id': purchase.partner_id.id,  # No calcula los related, tenemos que pasarlos en vals
                         'product_id': line.product_id.id,}
            line_vals.update(
                self.env['purchase.order.line'].play_onchanges(
                    line_vals, ['product_id']))
            self.env["purchase.order.line"].create(line_vals)

        view = self.env["ir.ui.view"].search(
            [('model', '=', "purchase.order"), ('type', '=', 'form')], limit=1)
        return {'name': _("Purchase Order"),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view.id,
                'res_model': "purchase.order",
                'res_id': self.purchase_id.id,
                'type': 'ir.actions.act_window'}
