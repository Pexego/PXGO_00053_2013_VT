# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class AddToPurchaseOrderWzd(models.TransientModel):

    _name = "add.to.purchase.order.wzd"

    @api.model
    def _get_manufacturer(self):
        product = self.env["product.product"].browse(
            self.env.context['active_ids'])
        return product.product_tmpl_id.manufacturer

    purchase_id = fields.Many2one("purchase.order", "Purchase")
    purchase_id_wt_manufacturer = fields.Many2one("purchase.order", "Purchase")
    custom_purchase_qty = fields.Boolean('Custom purchase qty')
    manufacturer = fields.Many2one(
        'res.partner', 'Manufacturer', readonly=True, invisible=False,
        default=_get_manufacturer)
    purchase_qty = fields.Float("Qty. to purchase")

    def assign_purchase_order(self):
        self.ensure_one()
        for product in self.env["product.product"].browse(
                self.env.context['active_ids']):
            purchase = self.purchase_id if self.purchase_id else \
                self.purchase_id_wt_manufacturer
            line_vals = {'order_id': purchase.id,
                         'partner_id': purchase.partner_id.id,  # No calcula los related, tenemos que pasarlos en vals
                         'product_id': product.id}
            if self.custom_purchase_qty:
                purchase_qty = self.purchase_qty
            else:
                min_suggested_qty = product.min_suggested_qty
                if min_suggested_qty < 0:
                    purchase_qty = -(product.min_suggested_qty)
                else:
                    purchase_qty = min_suggested_qty
            line_vals['product_uom_qty'] = purchase_qty
            line_vals.update(
                self.env['purchase.order.line'].play_onchanges(
                    line_vals, ['product_id']))
            self.env["purchase.order.line"].create(line_vals)

        return {'type': 'ir.actions.act_window_close'}
