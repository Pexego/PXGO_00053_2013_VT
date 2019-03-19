# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _


class CreatePurchaseFromUnsafetyWzd(models.TransientModel):

    _name = "create.purchase.from.unsafety.wzd"

    @api.model
    def default_get(self, fields_list):
        defaults = super(CreatePurchaseFromUnsafetyWzd, self).\
            default_get(fields_list)
        if self.env.context.get('active_id', False):
            for unsafety in self.env["product.stock.unsafety"].browse(
                    self.env.context['active_id']):
                if unsafety.supplier_id:
                    defaults['supplier_id'] = unsafety.supplier_id.id
                    defaults['warehouse_id'] = unsafety.orderpoint_id.\
                        warehouse_id.id
                    break
        return defaults

    supplier_id = fields.Many2one("res.partner", "Supplier", required=True,
                                  domain=[('supplier', '=', True),
                                          ('is_company', '=', True)])
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse",
                                   required=True)

    def create_purchase_order(self):
        self.ensure_one()
        purchase_vals = {'partner_id': self.supplier_id.id,
                         'picking_type_id': self.warehouse_id.in_type_id.id}
        purchase_vals.update(
                self.env['purchase.order'].play_onchanges(
                    purchase_vals, ['partner_id']))
        purchase = self.env["purchase.order"].create(purchase_vals)
        for line in self.env["product.stock.unsafety"].browse(
                self.env.context['active_ids']):
            line_vals = {'order_id': purchase.id,
                         'partner_id': purchase.partner_id.id,  # No calcula los related, tenemos que pasarlos en vals
                         'product_id': line.product_id.id}
            line_vals.update(
                self.env['purchase.order.line'].play_onchanges(
                    line_vals, ['product_id']))
            self.env["purchase.order.line"].create(line_vals)
            line.purchase_id = purchase.id
            line.state = "in_action"
            line.supplier_id = self.supplier_id.id

        view = self.env["ir.ui.view"].search(
            [('model', '=', "purchase.order"),
             ('type', '=', 'form')], limit=1)
        return {'name': _("Purchase Order"),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view.id,
                'res_model': "purchase.order",
                'res_id': purchase.id,
                'type': 'ir.actions.act_window'}
