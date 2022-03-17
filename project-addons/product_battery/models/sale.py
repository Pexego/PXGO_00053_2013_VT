from odoo import fields, models, _, exceptions, api


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    allow_ship_battery = fields.Boolean("Allow ship batteries")

    @api.multi
    def action_confirm(self):
        for sale in self:
            if not sale.allow_ship_battery:
                transport_service = sale.service_id
                msg = ''
                for line in sale.order_line:
                    if transport_service in line.product_id.battery_id.forbidden_ship_ids:
                        msg += "\n %s - %s" % (line.product_id.default_code, line.product_id.battery_id.name)
                if msg:
                    msg_error = _("\nThe order can not be confirmed, there are products with batteries that can not be shipped by %s") \
                           % transport_service.name
                    msg_error += msg
                    raise exceptions.UserError(msg_error)

        return super(SaleOrder, self).action_confirm()
