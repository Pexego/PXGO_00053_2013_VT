from odoo import fields, api, models, _, exceptions


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    allow_payment_term = fields.Boolean("Allow payment term")

    @api.multi
    def action_confirm(self):
        payment_term_immediate = self.env.ref('account.account_payment_term_immediate')
        max_payment_term = float(
            self.env['ir.config_parameter'].sudo().get_param('max.amount.in.payment.term'))
        for sale in self:
            if not sale.allow_payment_term and sale.payment_term_id == payment_term_immediate and sale.amount_total > max_payment_term:
                raise exceptions.UserError(
                    _("The order can not be confirmed, maximum amount exceeded for payment term selected"))

        return super(SaleOrder, self).action_confirm()
