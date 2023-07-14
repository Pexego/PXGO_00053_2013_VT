from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):

    _inherit = "sale.order"

    all_dropship = fields.Boolean("All Dropship")

    transporter_ds_id = fields.Many2one('res.partner', "Transporter", domain=[('is_transporter', '=', True)])
    service_ds_id = fields.Many2one('delivery.carrier', "Service")

    def action_confirm(self):
        res = super().action_confirm()
        for sale in self:
            if not sale.allow_ship_battery:
                transport_service = sale.service_ds_id
                msg = ''
                for line in sale.order_line:
                    if transport_service in line.product_id.battery_id.forbidden_ship_ids:
                        msg += "\n %s - %s" % (line.product_id.default_code, line.product_id.battery_id.name)
                if msg:
                    msg_error = _(
                        "\nThe order can not be confirmed, there are products with"
                        " batteries that can not be shipped by %s") % transport_service.name
                    msg_error += msg
                    raise UserError(msg_error)

            purchase = self.env['purchase.order'].search([('origin', '=', sale.name), ('state', '=', 'draft')])
            if purchase:
                if purchase.picking_type_id == self.env.ref('stock_dropshipping.picking_type_dropship'):
                    purchase.confirm_and_create_order_es()
        return res

    def action_cancel(self):
        res = super().action_cancel()
        purchase = self.env['purchase.order'].search([
            ('origin', '=', self.name), ('state', 'in', ('done', 'purchase'))
        ])
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

    @api.multi
    @api.onchange('transporter_ds_id')
    def onchange_transporter_ds_id(self):
        service_ids = [x.id for x in self.transporter_ds_id.carrier_ids]
        if service_ids:
            if self.service_ds_id.id not in service_ids:
                self.service_ds_id = False
            return {'domain': {'service_ds_id': [('id', 'in', service_ids)]}}
        all_services = [x.id for x in self.env['transportation.service'].search([])]
        return {'domain': {'service_ds_id': [('id', 'in', all_services)]}}


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.constrains('route_id', 'deposit')
    def check_deposit_dropship(self):
        dropship_route = self.env.ref('stock_dropshipping.route_drop_shipping').id
        for line in self:
            if line.route_id.id == dropship_route and line.deposit:
                raise ValidationError(
                    _('Error! A line cannot be dropship and deposit at the same time'))
        return True
