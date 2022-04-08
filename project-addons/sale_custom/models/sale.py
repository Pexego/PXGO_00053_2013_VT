# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, exceptions, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    description_editable_related = fields.Boolean(related='product_id.description_editable', readonly=1)

    select_copy = fields.Boolean(' ')

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

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not \
                self.product_uom:
            self.product_packaging = False
            return {}
        if self.order_id.state == 'sale':
            exception = self.order_id.check_weight(True)
            if exception:
                warning_mess =  {
                        'title': _('Max weight advise'),
                        'message': exception}
                return {'warning': warning_mess}
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].\
                precision_get('Product Unit of Measure')
            product = self.product_id.with_context(
                warehouse=self.order_id.warehouse_id.id,
                lang=self.order_id.partner_id.lang or self.env.user.lang or
                'en_US'
            )
            product_qty = self.product_uom.\
                _compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if float_compare(product.virtual_stock_conservative, product_qty,
                             precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    if self.product_id.replacement_id:
                        if self.product_id.replacement_id.virtual_stock_conservative-self.product_uom_qty >= 0 and self.product_id.replacement_id.sale_ok:
                            message = _('The quantity of the selected product (%i units) is not available at this moment but there is another product that can replace it: %s.') %(self.product_id.virtual_stock_conservative,self.product_id.replacement_id.default_code)
                            warning_mess = {
                                'title': _('Not enough inventory but we have a replacement product!'),
                                'message': message
                            }
                            return {'warning': warning_mess}
                    message =  \
                        _('You plan to sell %s %s but you only have %s %s '
                          'available in %s warehouse.') % \
                        (self.product_uom_qty, self.product_uom.name,
                         product.virtual_stock_conservative,
                         product.uom_id.name, self.order_id.warehouse_id.name)
                    if float_compare(product.virtual_stock_conservative,
                                     self.product_id.
                                     virtual_stock_conservative,
                                     precision_digits=precision) == -1:
                        message += \
                            _('\nThere are %s %s available accross all '
                              'warehouses.') % \
                            (self.product_id.virtual_stock_conservative,
                             product.uom_id.name)

                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message': message
                    }
                    return {'warning': warning_mess}
        return {}

    @api.multi
    def _update_reservation_price_qty(self):
        lines_released = self.env['sale.order.line']
        if not self.env.context.get('later', False):
            for line in self:
                if len(line.reservation_ids) > 1 or line.product_id.bom_ids:
                    line.reservation_ids.release()
                    lines_released += line
            super()._update_reservation_price_qty()
        if lines_released:
            lines_released.stock_reserve()


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
    not_sync_picking = fields.Boolean()
    pricelist_id = fields.Many2one(
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'reserve': [('readonly', False)]})
    force_generic_product = fields.Boolean(default= False)

    is_editable = fields.Boolean(compute='_get_is_editable', default=True)

    @api.multi
    def _get_is_editable(self):
        for order in self:
            order.is_editable = (self.env.user.has_group('sale_custom.sale_editor') and order.state == 'sale') \
                    or order.state in ('draft', 'sent', 'reserve')

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        # Load the favorite shipping address
        super().onchange_partner_id()
        if self.opportunity_id and self.opportunity_id.partner_id.parent_id:
            self.partner_id = self.opportunity_id.partner_id.commercial_partner_id
            self.partner_shipping_id = self.opportunity_id.partner_id
        for child in self.partner_id.child_ids:
            if child.default_shipping_address:
                self.partner_shipping_id = child.id
                break

    @api.onchange('pricelist_id')
    def reset_lines_price(self):
        for line in self.order_line:
            product = line.product_id
            line.price_unit = self.env['account.tax']._fix_tax_included_price_company(
                line._get_display_price(product), product.taxes_id, line.tax_id, self.company_id)
            line._onchange_discount()
            line.write({'old_discount': 0.0, 'accumulated_promo': False})
        if self.order_line and \
                self.pricelist_id and self.pricelist_id.discount_policy == 'with_discount':
            self.order_line.write({'discount': 0.0})

    def open_historical_orders(self):
        self.ensure_one()
        partner_id = self.partner_id.commercial_partner_id.id
        order_view_id = self.env.ref('sale.act_res_partner_2_sale_order').id
        last_order = self.env['sale.order'].search(
            [('id', '!=', self.id),
             ('partner_id', 'child_of', [partner_id]),
             ('state', 'not in', ['cancel', 'draft', 'sent'])],
            limit=1, order='date_order DESC').id
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        record_url = base_url + '/web/?#view_type=list&model=sale.order&action=' + \
            str(order_view_id) + '&active_id=' + str(partner_id)
        return {
            'name': 'Historical Partner Orders',
            'type': 'ir.actions.act_url',
            'view_type': 'form',
            'url': record_url,
            'target': 'new'
        }

    @api.multi
    def recalculate_line_prices(self):
        for order in self:
            for line in order.order_line:
                if line.original_line_id.discount >line.discount or not line.original_line_id:
                    line._onchange_discount()

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
        view_id = self.env.ref('sale_custom.view_financial_risk_res_partner_wizard').id

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
        self.validated_dir = True   # Validate the address to not break with flow

        listFields = []             # Dictionary to control all fields of address
        fields = {'Street': self.partner_shipping_id.street,
                  'Zip': self.partner_shipping_id.zip,
                  'City': self.partner_shipping_id.city,
                  'State': self.partner_shipping_id.state_id.id,
                  'Country': self.partner_shipping_id.country_id.id}

        if not all(fields.values()):
            warning = _('The address is incorrect, the following fields are empty:\n')  # warning message

            for key, value in fields.items():  # Rebuilt the list of fields
                if not value:
                    listFields.append(_(key))

            warning += ', '.join(listFields)   # Separate by commas

            self.env.user.notify_warning(message=warning, sticky=True)

    def action_confirm(self):
        if any(d.product_id.id == self.env.ref('product_product.generic_product').id for d in self.order_line) and not self.force_generic_product:
            raise UserError(_("You can't confirm a sale with the product %s.")%(next(item.product_id.name for item in self.order_line if item.product_id.id == 17897)))
        if not self.env.context.get('bypass_override', False) and (
                not self.env.context.get('bypass_risk', False) or self.env.context.get('force_check', False)):
            user_buyer = self.env['ir.config_parameter'].sudo().get_param(
                'web.user.buyer')
            for sale in self:
                exception = sale.check_weight()
                if exception:
                    return exception
                if not sale.validated_dir and sale.create_uid.email == \
                        user_buyer and self.delivery_type not in 'installations':
                    message = _('Please, validate shipping address.')
                    raise exceptions.Warning(message)

                shipping_cost_line = False
                if self.delivery_type not in ('installations', 'carrier'):
                    for line in self.order_line:
                        if line.product_id.categ_id.with_context(lang='es_ES').name == 'Portes':
                            shipping_cost_line = True
                    if not shipping_cost_line:
                        message = _('Please, introduce a shipping cost line.')
                        raise exceptions.Warning(message)

                self.apply_commercial_rules()

                if not sale.is_all_reserved and 'confirmed' not in \
                        self.env.context:
                    message = "Some of the products of this order {} aren't available now".format(self.name)
                    self.env.user.notify_info(title="Please consider that!",
                                              message=message)
        res = super().action_confirm()

        if isinstance(res, bool):
            for sale in self:
                products_to_order = ''
                for line in sale.order_line.filtered(lambda l: l.product_id.state == 'make_to_order'):
                    products_to_order = products_to_order + \
                                        line.product_id.default_code + ' -> ' + \
                                        str(line.product_uom_qty) + '    '
                if products_to_order:
                    sale.send_email_to_purchases(products_to_order)

        if self.not_sync_picking:
            for picking in self.picking_ids:
                picking.not_sync = True

        return res

    @api.multi
    def send_email_to_purchases(self, products_to_order):
        self.ensure_one()
        mail_pool = self.env['mail.mail']
        context = self._context.copy()
        context['base_url'] = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        context['products_to_order'] = products_to_order
        context.pop('default_state', False)

        template_id = self.env.ref('sale_custom.email_template_purchase_product_to_order')

        if template_id:
            mail_id = template_id.with_context(context).send_mail(self.id)
            if mail_id:
                mail_id_check = mail_pool.browse(mail_id)
                mail_id_check.with_context(context).send()

        return True

    def check_weight(self, onchange=False):
        dhl_flight = self.transporter_id.name == "DHL" and self.service_id.by_air
        canary = self.partner_shipping_id and \
                 not self.env.context.get("bypass_canary_max_weight", False) and \
                 self.partner_shipping_id.state_id.id in (
                 self.env.ref("base.state_es_tf").id, self.env.ref("base.state_es_gc").id)
        if dhl_flight or canary:
            dhl_max_weight = self.env['ir.config_parameter'].sudo().get_param('dhl_max_weight')
            canary_max_weight = self.env['ir.config_parameter'].sudo().get_param('canary_max_weight')
            products_weight = 0
            for line in self.order_line:
                if isinstance(line.id, int):
                    products_weight += line.product_id.weight * line.product_uom_qty
            if dhl_flight and products_weight > float(dhl_max_weight):
                message = _('Sale has been blocked due to exceed the weight limit in DHL air shipments.')
                raise exceptions.Warning(message)
            if canary and products_weight > float(canary_max_weight):
                if onchange:
                    return _(
                        "This order to the Canary Islands exceeds %skg. Have you checked the shipping costs and conditions?" % canary_max_weight)
                return self.env['max.weight.advise.wiz'].create({
                    'sale_id': self.id,
                    'origin_reference':
                        '%s,%s' % ('sale.order', self.id),
                    'continue_method': 'action_confirm',
                    'message': _(
                        "This order to the Canary Islands exceeds %skg. Have you checked the shipping costs and conditions?") % canary_max_weight
                }).action_show()

    @api.multi
    def copy_sale_lines(self):
        for order in self:
            for line in order.order_line:
                if line.select_copy:
                    line.copy({'order_id': order.id,
                               'select_copy': False})
                    line.select_copy = False


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
