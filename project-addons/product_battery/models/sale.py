from odoo import fields, models, _, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    allow_ship_battery = fields.Boolean("Allow ship batteries", copy=False)

    @api.multi
    def action_confirm(self):
        for sale in self:
            if not sale.allow_ship_battery:
                delivery_carrier = sale.carrier_id
                msg = ''
                for line in sale.order_line:
                    if delivery_carrier in line.product_id.battery_id.forbidden_ship_ids:
                        msg += "\n %s - %s" % (
                            line.product_id.default_code,
                            line.product_id.battery_id.name
                        )
                if msg:
                    msg_error = _(
                        "\nThe order can not be confirmed, there are products"
                        " with batteries that can not be shipped by %s") % delivery_carrier.name
                    msg_error += msg
                    raise UserError(msg_error)

        return super(SaleOrder, self).action_confirm()
