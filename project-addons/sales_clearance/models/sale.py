from odoo import models, fields, api, exceptions, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    allow_payment_term = fields.Boolean("Allow payment term", copy=False)

    @api.multi
    def action_confirm(self):
        """
            Override original method to check for payment term-related exceptions.
        """
        self.check_payment_term_exceptions()
        return super(SaleOrder, self).action_confirm()

    @api.multi
    def check_payment_term_exceptions(self):
        """
            Check for payment term related exceptions in the sales order.
        """
        for sale in self:
            if not sale.allow_payment_term:
                if sale.partner_id.credit_limit:
                    sale._check_credit_limit_exceeded()
                else:
                    sale._check_payment_term_exceeded()

    def _check_credit_limit_exceeded(self):
        """
            Check if the credit limit has been exceeded for the sales order.
        """
        max_risk_percentage = float(self.env['ir.config_parameter'].sudo().get_param('max.risk.percentage.in.payment.term'))
        max_payment_term = float(self.env['ir.config_parameter'].sudo().get_param('max.amount.in.payment.term'))
        for sale in self:
            amount_total = sale.amount_total
            max_credit_limit_amount = sale.partner_id.credit_limit * (max_risk_percentage / 100)
            is_immediate_payment = sale.payment_term_id.with_context({'lang': 'es_ES'}).name == 'Pago inmediato'
            if is_immediate_payment and (amount_total > max_payment_term or amount_total > max_credit_limit_amount):
                raise exceptions.UserError(
                    _("The order cannot be confirmed. The maximum amount for the selected payment term has been exceeded."))

    def _check_payment_term_exceeded(self):
        """
            Check if the payment term has been exceeded for the sales order.
        """
        for sale in self:
            max_payment_term = float(self.env['ir.config_parameter'].sudo().get_param('max.amount.in.payment.term'))
            payment_term_name = sale.payment_term_id.with_context({'lang': 'es_ES'}).name
            if payment_term_name in ('Prepago', 'Pago inmediato') and sale.amount_total > max_payment_term:
                raise exceptions.UserError(
                    _("The order cannot be confirmed. The maximum amount for the selected payment term has been exceeded."))
