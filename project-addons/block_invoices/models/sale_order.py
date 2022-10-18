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

    def check_partners_exceptions(self, partners):
        message = ''
        for partner in partners:
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

    def check_order_exceptions(self):
        magreb_limit = int(self.env['ir.config_parameter'].sudo().get_param('magreb.limit.without.block'))
        margin_limit = self.env['ir.config_parameter'].sudo().get_param('margin.lock.limit')
        for order in self:
            if order.amount_total >= magreb_limit \
                and (order.team_id.name == 'Magreb' or order.partner_id.team_id.name == 'Magreb') \
                and not order.allow_confirm_blocked_magreb:
                raise exceptions.Warning(_('Order blocked. Approve pending'))
            if not order.pricelist_id.name.startswith('PVI'):
                margin_adj = float(order.get_margin_adjustment())
                if margin_adj <= 0.0:
                    margin_adj = order.margin_rappel
                if margin_adj < int(margin_limit) and not self.allow_confirm_blocked_magreb:
                    # we use the same check to aprove that magreb
                    message = _('Order blocked. Approve pending, margin is below the limits.')
                    raise exceptions.Warning(message)
    def get_margin_adjustment(self):
        margin = 0.0
        sale_price = 0.0
        purchase_price = 0.0
        for line in self.order_line.filtered(lambda l: not l.deposit and not l.promotion_line and not l.product_id.exclude_margin):
            if line.price_unit > 0:
                margin += line.margin_rappel or 0.0
            else:
                margin += (line.price_unit * line.product_uom_qty) * ((100.0 - line.discount) / 100.0)
            sale_price += line.price_subtotal or 0.0
            purchase_price += (line.product_id.standard_price_2_inc or 0.0) * line.product_uom_qty
        if sale_price > 0:
            if sale_price < purchase_price:
                margin = round((margin * 100) / purchase_price, 2)
            else:
                margin = round((margin * 100) / sale_price, 2)
        return margin

    @api.multi
    def action_confirm(self):
        if not self.env.context.get('bypass_risk', False) or self.env.context.get('force_check', False):
            partners = self.partner_id.get_partners_to_check()
            self.check_partners_exceptions(partners)
            self.check_order_exceptions()
        return super().action_confirm()
