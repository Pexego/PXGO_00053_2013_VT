# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, exceptions, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    def write(self, vals):
        for line in self:
            if vals.get('product_id', False):
                product = self.env['product.product'].browse(
                    vals['product_id'])
                vals['name'] = product.name_get()[0][1]
                if product.description_sale:
                    vals['name'] += '\n' + product.description_sale
        return super().write(vals)

    @api.onchange('product_id')
    def product_id_change_check_zero_quantity(self):
        if self.product_uom_qty <= 0:
            raise UserError(_('Product quantity cannot be negative or zero'))


class SaleOrder(models.Model):

    _inherit = "sale.order"

    validated_dir = fields.Boolean(default=False)

    partner_id = fields.Many2one(
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reserve': [('readonly', False)]},)
    partner_invoice_id = fields.Many2one(
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reserve': [('readonly', False)]})
    partner_shipping_id = fields.Many2one(
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reserve': [('readonly', False)]})
    warehouse_id = fields.Many2one(
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reserve': [('readonly', False)]})
    picking_policy = fields.Selection(
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reserve': [('readonly', False)]})

    def onchange_partner_id(self):
        """
            TODO: Por qué es necesario?
        """
        val = super().onchange_partner_id()
        for child in self.partner_id.child_ids:
            if child.default_shipping_address:
                val['value']['partner_shipping_id'] = child.id
                break

        return val

    def open_historical_orders(self):
        self.ensure_one()
        partner_id = self.partner_id.commercial_partner_id.id
        order_view_id = self.env.ref('sale.act_res_partner_2_sale_order').id
        last_order = self.env['sale.order'].search(
            [('id', '!=', self.id),
             ('partner_id', 'child_of', [partner_id]),
             ('state', 'not in', ['cancel', 'draft', 'sent'])],
            limit=1, order='date_order DESC').id
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        record_url = base_url + '/web/?#id=' + str(last_order) + \
            '&view_type=form&model=sale.order&action=' + \
            str(order_view_id) + '&active_id=' + str(partner_id)
        return {
            'name': 'Historical Partner Orders',
            'type': 'ir.actions.act_url',
            'view_type': 'form',
            'url': record_url,
            'target': 'new'
        }

    @api.multi
    def button_notification(self):

        res_partner_id = self.partner_id
        view_id = self.env.ref('sale_custom.view_warning_form').id  # Id asociado a esa vista

        return {
            'name': _('Warnings'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.partner',
            'view_id': view_id,
            'res_id': res_partner_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'flags': {'form': {'options': {'mode': 'view'}}}
        }

    @api.multi
    def button_notification_open_risk_window(self):
        partner_id = self.partner_id
        view_id = self.env.ref('nan_partner_risk.open_risk_window_view').id

        return {
            'name': _('Partner Risk Information'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.partner',
            'view_id': view_id,
            'res_id': partner_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'flags': {'form': {'options': {'mode': 'view'}}}
        }

    def validate_address(self):
        self.ensure_one()
        self.validated_dir = True

    def action_confirm(self):
        user_buyer = self.env['ir.config_parameter'].get_param(
            'web.user.buyer')
        for sale in self:
            if not sale.validated_dir and sale.create_uid.email == user_buyer:
                message = _('Please, validate shipping address.')
                raise exceptions.Warning(message)

            shipping_cost_line = False
            if self.delivery_type not in ('installations', 'carrier'):
                for line in self.order_line:
                    if line.product_id.categ_id.name == 'Portes':
                        shipping_cost_line = True
                if not shipping_cost_line:
                    message = _('Please, introduce a shipping cost line.')
                    raise exceptions.Warning(message)

        return super().action_confirm()


class MailMail(models.Model):
    _inherit = 'mail.mail'

    # This allows to save the sale order with the state reserve
    @api.model
    def create(self, vals):
        context = dict(self.env.context)
        context.pop('default_state', False)
        self = self.with_context(context)
        return super(MailMail, self).create(vals)


class StockMove(models.Model):
    _inherit = 'stock.move'

    # This allows to save the sale order with the state reserve
    @api.model
    def create(self, vals):
        context = dict(self.env.context)
        context.pop('default_state', False)
        self = self.with_context(context)
        return super(StockMove, self).create(vals)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # This allows to save the sale order with the state reserve
    @api.model
    def create(self, vals):
        context = dict(self.env.context)
        context.pop('default_state', False)
        self = self.with_context(context)
        return super(StockMoveLine, self).create(vals)

