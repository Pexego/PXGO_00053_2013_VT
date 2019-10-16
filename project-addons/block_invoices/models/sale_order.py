# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, exceptions, api, _


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    blocked = fields.Boolean(
        related='partner_id.commercial_partner_id.blocked_sales')
    defaulter = fields.Boolean(
        related='partner_id.commercial_partner_id.defaulter')
    allow_confirm_blocked = fields.Boolean('Allow confirm', copy=False)
    allow_confirm_blocked_magreb = fields.Boolean('Allow confirm', copy=False)

    @api.onchange('partner_id')
    def onchange_partner_id_check_blocked(self):
        """
            Comprueba si el cliente del pedido de venta está bloqueado
            antes de efectuar ninguna venta
        """
        warning = {}
        title = False
        message = False
        # Compruebo la empresa actual y su padre...
        partners_to_check = self.partner_id.get_partners_to_check()
        for partner in partners_to_check:
            if partner.defaulter:
                title = _("Warning for %s") % partner.name
                message = _('Defaulter customer! Please contact the \
                    accounting department.')
                warning = {
                    'title': title,
                    'message': message,
                }
            elif partner.blocked_sales:
                title = _("Warning for %s") % partner.name
                message = _('Customer blocked by lack of payment. Check the \
                    maturity dates of their account move lines.')
                warning = {
                        'title': title,
                        'message': message,
                }
            return {'warning': warning}

    @api.multi
    def _action_confirm(self):
        message = ''
        for partner in self.partner_id.get_partners_to_check():
            if partner.blocked_sales and not self.allow_confirm_blocked:
                message = _('Customer %s blocked by lack of payment. Check '
                            'the maturity dates of their account move '
                            'lines.') % partner.name
            elif partner.defaulter:
                message = _('Defaulter customer! Please contact the accounting department.')
            elif partner.customer_payment_mode_id.name == 'Recibo domiciliado' and \
                    len(partner.bank_ids) == 0:
                message = _('Order blocked. The client has not bank account.')

            if message:
                raise exceptions.Warning(message)

        if (self.team_id.name == 'Magreb' or self.partner_id.team_id.name == 'Magreb') \
                and not self.allow_confirm_blocked_magreb:
            message = _('Order blocked. Approve pending')
            raise exceptions.Warning(message)

        if not self.pricelist_id.name.startswith('PVI'):
            for line in self.order_line:
                if line.margin_perc_rappel < 10 and not line.deposit and not line.promotion_line and line.product_id.state != 'end' and line.product_id.categ_id.id not in (392, 393, 468) and not self.allow_confirm_blocked_magreb:
                    # we use the same check to aprove that magreb
                    message = _('Order blocked. Approve pending, margin is below the limits.')
                    raise exceptions.Warning(message)

        return super()._action_confirm()
