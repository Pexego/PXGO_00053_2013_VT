from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.onchange("delivery_type")
    def _compute_is_special_shipping_costs(self):
        """
        Checks if the sale_order has special shipping costs
        """
        for order in self:
            order.is_special_shipping_costs = (
                order.delivery_type == 'shipping' and order.order_line
                and order.order_line.filtered(lambda l: l.product_id.special_shipping_costs)
            )

    is_special_shipping_costs = fields.Boolean(compute="_compute_is_special_shipping_costs", store=True)

    @api.multi
    def _get_email_advise(self):
        advise = self.env['ir.config_parameter'].sudo().get_param('advise_special_shipping_email')
        for sale in self:
            sale.advise_email = advise

    advise_email = fields.Char(compute="_get_email_advise")

    @api.multi
    def _write(self, vals):
        transporter_id = self.env.ref('advise_special_shipping_costs.palletized_shipping_transporter', False)
        for order in self:
            if vals.get('is_special_shipping_costs', False):
                vals['delivery_type'] = 'shipping'
                vals['transporter_id'] = transporter_id.id
                vals['carrier_id'] = self.env.ref('advise_special_shipping_costs.palletized_shipping_service').id
            elif (
                'is_special_shipping_costs' in vals
                and
                order.transporter_id == transporter_id
                and
                order.is_special_shipping_costs != vals.get('is_special_shipping_costs')
            ):
                vals['delivery_type'] = order.partner_id.delivery_type
                vals['transporter_id'] = order.partner_id.transporter_id.id
                vals['carrier_id'] = order.partner_id.property_delivery_carrier_id.id
        return super()._write(vals)

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        for order in self:
            if 'order_line' in vals:
                order._compute_is_special_shipping_costs()
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._compute_is_special_shipping_costs()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange("product_id")
    def _compute_is_special_shipping_costs(self):
        """
        Checks if the sale_order has special shipping costs
        """
        for line in self:
            needs_to_be_calculated = (
                line.order_id.delivery_type == 'shipping'
                and line.product_id.special_shipping_costs
            )
            if needs_to_be_calculated:
                line.order_id._compute_is_special_shipping_costs()
