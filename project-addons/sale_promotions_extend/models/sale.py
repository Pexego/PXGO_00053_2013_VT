# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _compute_product_tags(self):
        for line in self:
            stream = []
            if line.product_id and line.product_id.tag_ids:
                tags = line.product_id.tag_ids._get_tag_recursivity()
                for tag in tags:
                    stream.append(tag.name)
            if stream:
                line.product_tags = stream
            else:
                line.product_tags = ''

    product_tags = fields.Char(compute="_compute_product_tags", string='Tags')
    web_discount = fields.Boolean()
    accumulated_promo = fields.Boolean(default=False)


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

        if not order.no_promos:
            res = super(SaleOrder, order).apply_commercial_rules()
        else:
            self.clear_existing_promotion_lines()
            self.env['promos.rules'].apply_special_promotions()
            res = False

        if order.state == 'reserve':
            order.order_reserve()

        taxes = order.order_line.filtered(
            lambda l: len(l.tax_id) > 0)[0].tax_id
        for line in order.order_line:
            if line.promotion_line:
                line.tax_id = taxes
                if '3 por ciento' in line.name:
                    line.sequence = 999
        return res

    def clear_existing_promotion_lines(self):
        line_dict = {}
        for line in self.order_line:
            line_dict[line.id] = line.old_discount

        res = super(SaleOrder, self).clear_existing_promotion_lines()

        for line in self.order_line:
            # if the line has an accumulated promo and the
            # discount of the partner is 0
            if line.accumulated_promo and line_dict[line.id] == 0.0:
                line.write({'discount': line.old_discount,
                            'old_discount': 0.00,
                            'accumulated_promo': False})
            elif line.accumulated_promo:
                line.write({'accumulated_promo': False})
        return res
