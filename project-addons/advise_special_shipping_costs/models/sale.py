from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.depends("order_line.product_id")
    def _compute_is_special_shipping_costs(self):
        for order in self:
            order.is_special_shipping_costs = order.order_line and order.order_line.filtered(
                lambda l: l.product_id.special_shipping_costs)

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
        if transporter_id and vals.get('is_special_shipping_costs', False):
            vals['delivery_type'] = 'shipping'
            vals['transporter_id'] = transporter_id.id
            vals['service_id'] = self.env.ref('advise_special_shipping_costs.palletized_shipping_service').id
        elif transporter_id and 'is_special_shipping_costs' in vals.keys() and self.transporter_id==transporter_id:
            vals['delivery_type'] = self.partner_id.delivery_type
            vals['transporter_id'] = self.partner_id.transporter_id.id
            vals['service_id'] = self.partner_id.service_id.id
        return super()._write(vals)


