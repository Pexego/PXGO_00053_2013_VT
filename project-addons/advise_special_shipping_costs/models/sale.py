from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.depends("order_line.product_id")
    def _compute_is_special_shipping_costs(self):
        for order in self:
            order.is_special_shipping_costs = order.order_line and order.order_line.filtered(
                lambda l: l.product_id.special_shipping_costs)

    is_special_shipping_costs = fields.Boolean(compute="_compute_is_special_shipping_costs",store=True)

    @api.multi
    def _write(self, vals):
        if vals.get('is_special_shipping_costs', False):
            vals['transporter_id'] = self.env.ref('advise_special_shipping_costs.palletized_shipping_transporter').id
            vals['service_id'] = self.env.ref('advise_special_shipping_costs.palletized_shipping_service').id
        return super()._write(vals)


