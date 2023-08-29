from odoo import models, fields, api, exceptions, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    allow_payment_term = fields.Boolean("Allow payment term", copy=False)

    @api.multi
    def action_confirm(self):
        max_payment_term = float(
            self.env['ir.config_parameter'].sudo().get_param('max.amount.in.payment.term'))
        for sale in self:
            if not sale.allow_payment_term and sale.payment_term_id.with_context({'lang': 'es_ES'}).name in (
                'Prepago', 'Pago inmediato') and sale.partner_id.property_payment_term_id.with_context(
                    {'lang': 'es_ES'}).name in ('Prepago', 'Pago inmediato') and sale.amount_total > max_payment_term:
                raise exceptions.UserError(
                    _("The order can not be confirmed, maximum amount exceeded for payment term selected"))

        return super(SaleOrder, self).action_confirm()
