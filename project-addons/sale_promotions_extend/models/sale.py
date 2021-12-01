# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _compute_product_tags(self):
        for line in self:
            stream = []
            if line.product_id and line.product_id.tag_ids:
                tags = line.product_id.tag_ids._get_tag_recursivity()
                for tag in tags:
                    stream.append(tag)
            line.product_tags = stream


    product_tags = fields.Char(compute="_compute_product_tags", string='Tags')
    web_discount = fields.Boolean()
    accumulated_promo = fields.Boolean(default=False)
    original_line_id_promo = fields.Integer("Original line")
    promo_qty_split = fields.Integer(help="It is the minimum quantity of product for which this promo is applied")
    old_discount = fields.Float(copy=False)
    old_price = fields.Float(copy=False)
    old_qty = fields.Float(copy=False)

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        lines = self.env['sale.order.line']
        for line in self:
            if line.price_unit < 0:
                order = line.order_id
                total_to_invoice_dict = self._context.get('total_to_invoice', False)
                total_to_invoice = 0
                # Do not include the discount lines if the qty to invoice is < 0
                # because it will create a refund
                if total_to_invoice_dict:
                    total_to_invoice = total_to_invoice_dict.get(self.order_id.id, 0)
                if total_to_invoice >= 0:
                    lines += line
                if total_to_invoice < 0 and all(oline.product_id.type == 'service'
                                                for oline in order.order_line.filtered(lambda l: l.invoice_status == 'to invoice')):
                    invoice = self.env['account.invoice'].browse(invoice_id)
                    if (invoice.type == 'out_refund' or not invoice.invoice_line_ids) and len(self) == 1:
                        return super(SaleOrderLine, line).invoice_line_create(invoice_id, -qty)
            else:
                lines += line
        return super(SaleOrderLine, lines).invoice_line_create(invoice_id, qty)

    @api.multi
    def _prepare_invoice_line(self, qty):
        if all(oline.product_id.type == 'service' for oline in
               self.order_id.order_line.filtered(lambda l: l.invoice_status == 'to invoice')) \
                and self.price_unit < 0:
            # This case is for creating a refund with the last discount on the order and positive quantities
            vals = super(SaleOrderLine, self)._prepare_invoice_line(qty)
            vals['price_unit'] = -vals['price_unit']
        else:
            vals = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        return vals

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        super()._get_invoice_qty()
        for line in self.filtered(lambda l: l.product_id.id == self.env.ref('commercial_rules.product_discount').id):
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    if invoice_line.invoice_id.type == 'out_invoice':
                        qty_invoiced += invoice_line.uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
                    elif invoice_line.invoice_id.type == 'out_refund' and line.price_unit < 0:
                        qty_invoiced += invoice_line.uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
            line.qty_invoiced = qty_invoiced

    @api.multi
    def write(self,vals):
        product_uom_qty = vals.get('product_uom_qty',False)
        for line in self:
            if product_uom_qty and not 'old_qty' in vals and line.old_qty:
                vals['old_qty'] = product_uom_qty
        return super(SaleOrderLine, self).write(vals)


class SaleOrder(models.Model):

    _inherit = "sale.order"

    no_promos = fields.Boolean(
        "Not apply promotions",
        help="Reload the prices after marking this check")

    def apply_commercial_rules(self):
        context2 = dict(self._context)
        context2.pop('default_state', False)
        self.with_context(context2)._prepare_custom_line(moves=False)
        order = self.with_context(context2)

        if order.state == 'reserve':
            # We need to do this because it fails when we apply promotions over
            # a kit with more than one component
            order.release_multiple_reservation_lines()

        if not order.no_promos:
            res = super(SaleOrder, order).apply_commercial_rules()
        else:
            self.clear_existing_promotion_lines()
            self.env['promos.rules'].apply_special_promotions(self)
            res = False

        taxes = order.order_line.filtered(
            lambda l: len(l.tax_id) > 0)[0].tax_id
        for line in order.order_line:
            if line.promotion_line:
                line.tax_id = taxes
                if '3 por ciento' in line.name:
                    line.sequence = 999
        return res

    def release_multiple_reservation_lines(self):
        for line in self.order_line:
            if len(line.reservation_ids) > 1:
                line.reservation_ids.release()

    def clear_existing_promotion_lines(self):
        line_dict = {}
        for line in self.order_line:
            line_dict[line.id] = line.old_discount

        res = super(SaleOrder, self).clear_existing_promotion_lines()

        for line in self.order_line:
            # if the line has an accumulated promo and the
            # discount of the partner is 0
            if line.old_price:
                line.write({'price_unit': line.old_price,
                            'old_price': 0.00})
            if line.accumulated_promo and line_dict[line.id] == 0.0:
                line.write({'discount': line.old_discount,
                            'old_discount': 0.00,
                            'accumulated_promo': False})
            elif line.accumulated_promo:
                line.write({'discount': line.old_discount,
                            'old_discount': 0.00,
                            'accumulated_promo': False})
            elif line.old_qty:
                line.write({'product_uom_qty':line.old_qty,
                            'old_qty':0})
        return res

    @api.multi
    def action_confirm(self):
        ctx = dict(self._context)
        ctx['is_confirm'] = True
        order = self.with_context(ctx)
        return super(SaleOrder, order).action_confirm()

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        ctx = dict(self.env.context)
        total_to_invoice_dict = {}
        for order in self:
            total_to_invoice = sum(order.order_line.filtered(lambda l: l.invoice_status == 'to invoice').mapped('amt_to_invoice'))
            total_to_invoice_dict[order.id] = total_to_invoice
        ctx.update({'total_to_invoice': total_to_invoice_dict})
        return super(SaleOrder, self.with_context(ctx)).action_invoice_create(grouped=grouped, final=final)

