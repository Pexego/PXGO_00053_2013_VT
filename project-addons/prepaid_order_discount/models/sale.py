# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, exceptions, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    prepaid_option = fields.Boolean("Prepaid option")

    @api.multi
    def action_confirm(self):
        risk = False
        for sale in self:
            message = ''
            if sale.prepaid_option:
                risk = True
                prepaid_discount_product_id = self.env.ref('prepaid_order_discount.prepaid_discount_product').id
                exist_prepaid_discount_line = sale.order_line. \
                    filtered(lambda l: l.product_id.id == prepaid_discount_product_id)
                if not exist_prepaid_discount_line:
                    message = _("It's an order with prepaid option. "
                                "Please, calculate the discount if partner has prepaid or cancel the prepaid option.")
                else:
                    order_lines_sorted_by_id = sale.order_line.sorted(key=lambda l: l.id)
                    last_product_order = order_lines_sorted_by_id[-1]
                    if exist_prepaid_discount_line.id < last_product_order.id:
                        # cálculamos el número de elementos que hay despues de la línea de descuento prepago
                        num_elements = len(order_lines_sorted_by_id) - 1 - order_lines_sorted_by_id.mapped('id').index(
                            exist_prepaid_discount_line.id)
                        last_elements = order_lines_sorted_by_id[-num_elements:]
                        # Si las líneas creadas posteriormente al descuento prepago no son ni gastos de envío, ni promos ,
                        # ni una línea asociada a otra que sea posterior al descuento por prepago hay que recalcular el descuento prepago
                        if num_elements >= 1 and any(line.product_id.categ_id.with_context(
                                lang='es_ES').name != 'Portes' and not line.promotion_line and not line.original_line_id in last_elements
                                                     for line in last_elements):
                            message = _("Please, recalculate prepaid discount")
            if message:
                raise exceptions.Warning(message)
        if risk:
            return super(SaleOrder, self.with_context(bypass_risk=True, force_check=True)).action_confirm()
        else:
            return super().action_confirm()

    @api.multi
    def calculate_prepaid_discount(self):
        # Comprobar qué descuento le corresponde
        # Si margen_pedido < margin_discount_1 -> No le corresponde descuento
        # Si margin_1 < margen_pedido < margin_2 -> Le corresponde descuento discount_1
        # Si margin_2 < margen_pedido < margen_3 -> Le corresponde descuento_2
        # Si margen_pedido > margin_3 -> Le corresponde descuento discount_3
        margin_discount_1 = self.env['ir.config_parameter'].sudo().get_param('minimum_margin.discount_perc.prepaid_1')
        margin_discount_2 = self.env['ir.config_parameter'].sudo().get_param('minimum_margin.discount_perc.prepaid_2')
        margin_discount_3 = self.env['ir.config_parameter'].sudo().get_param('minimum_margin.discount_perc.prepaid_3')
        prepaid_discount_product_id = self.env.ref('prepaid_order_discount.prepaid_discount_product').id
        shipping_cost_categ = self.env['product.category']. \
            with_context(lang='es_ES').search([('name', '=', 'Portes')])
        daily_invoicing = self.env['res.partner.invoice.type'].search([('name', '=', 'Diaria')])
        for sale in self:
            # Comprobar que el plazo de pago del cliente no sea prepago por defecto,
            # en cuyo caso no le corresponde este descuento
            if sale.partner_id.prepaid_payment_term():
                sale.cancel_prepaid_option()
                message = _("The prepayment discount cannot be applied due to the customer's payment mode")
                self.env.user.notify_info(title=_("Prepaid discount cancelled"),
                                          message=message)
                continue
            # Borrar línea descuento prepago existente
            sale.order_line.filtered(lambda l: l.product_id.id == prepaid_discount_product_id).unlink()
            # Aplicar promociones
            sale.apply_commercial_rules()
            # Obtener umbrales márgenes y porcentaje descuento a aplicar
            margin_sale = sale.product_margin_without_shipping_costs(shipping_cost_categ)

            margin_1 = int(margin_discount_1.split(',')[0])
            discount_1 = margin_discount_1.split(',')[1]
            margin_2 = int(margin_discount_2.split(',')[0])
            discount_2 = margin_discount_2.split(',')[1]
            margin_3 = int(margin_discount_3.split(',')[0])
            discount_3 = margin_discount_3.split(',')[1]

            amount_untaxed = sum(sale.order_line.filtered(
                lambda l: l.product_id.categ_id.id not in shipping_cost_categ.ids).mapped('price_subtotal'))

            def create_prepaid_discount_line(discount):
                last_sequence = sale.order_line.sorted(lambda l: l.sequence)[-1].sequence
                discount_line_vals = {'order_id': sale.id,
                                      'product_id': prepaid_discount_product_id,
                                      'name': _("%s prepaid discount") % (discount + '%'),
                                      'product_uom_qyt': 1.0,
                                      'price_unit': -(amount_untaxed * int(discount) / 100),
                                      'sequence': last_sequence + 1}
                self.env['sale.order.line'].create(discount_line_vals)
                # Se pone como método de pago "Pago Inmediato" y facturación "Diaría"
                sale.payment_term_id = self.env.ref('account.account_payment_term_immediate').id
                if sale.payment_mode_id.name == 'Ricevuta bancaria':
                    sale.payment_mode_id = self.env['account.payment.mode'].search(
                        [('payment_method_code', '=', 'MP05')])
                sale.invoice_type_id = daily_invoicing.id

            if margin_1 <= margin_sale < margin_2:
                create_prepaid_discount_line(discount_1)
            elif margin_2 <= margin_sale < margin_3:
                create_prepaid_discount_line(discount_2)
            elif margin_sale >= margin_3:
                create_prepaid_discount_line(discount_3)
            else:
                message = _("The order margin are below the limits to apply the prepayment discount")
                self.env.user.notify_info(title=_("Prepaid discount line has not been created"),
                                          message=message)
        return True

    @api.multi
    def cancel_prepaid_option(self):
        for sale in self:
            # Borrar línea descuento prepago existente
            prepaid_discount_product_id = self.env.ref('prepaid_order_discount.prepaid_discount_product').id
            sale.order_line.filtered(lambda l: l.product_id.id == prepaid_discount_product_id).unlink()
            # Marcar check prepaid_discount = False
            sale.prepaid_option = False
            # Poner plazo de pago y tipo de facturación con los datos del cliente
            sale.payment_term_id = sale.partner_id.property_payment_term_id
            sale.invoice_type_id = sale.partner_id.invoice_type_id
        return True

    @api.multi
    def product_margin_without_shipping_costs(self, shipping_cost_categ):
        for sale in self:
            margin_rappel = 0.0
            sale_price = 0.0
            purchase_price = 0.0
            generic_product = self.env.ref('sale_margin_percentage.generic_product').id
            for line in sale.order_line.filtered(lambda l: l.product_id.id != generic_product and not l.deposit
                              and l.product_id.categ_id.id not in shipping_cost_categ.ids and not l.original_line_id):
                if line.price_unit > 0:
                    margin_rappel += line.margin_rappel or 0.0
                else:
                    margin_rappel += (line.price_unit * line.product_uom_qty) * ((100.0 - line.discount) / 100.0)
                sale_price += line.price_subtotal or 0.0
                purchase_price += line.product_id.standard_price_2_inc or 0.0 * line.product_uom_qty
            if sale_price:
                if sale_price < purchase_price:
                    return round((margin_rappel * 100) / purchase_price, 2)
                else:
                    return round((margin_rappel * 100) / sale_price, 2)

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if vals.get('prepaid_option', False) and self.env.user.login == self.env[
            'ir.config_parameter'].sudo().get_param(
            'web.user.buyer'):
            res.message_post(body=_("Prepaid option checked by Web Team"))
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _get_products_non_editable(self):
        res = super()._get_products_non_editable()
        res.append(self.env.ref("prepaid_order_discount.prepaid_discount_product").id)
        return res

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        super()._get_invoice_qty()
        for line in self.filtered(lambda l: l.product_id.id == self.env.ref('prepaid_order_discount.prepaid_discount_product').id):
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    if invoice_line.invoice_id.type == 'out_invoice':
                        qty_invoiced += invoice_line.uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
                    elif invoice_line.invoice_id.type == 'out_refund' and line.price_unit < 0:
                        qty_invoiced += invoice_line.uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
            line.qty_invoiced = qty_invoiced