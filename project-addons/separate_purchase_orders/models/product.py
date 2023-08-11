from odoo import models, fields, api
from collections import defaultdict

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def _get_in_production_stock(self):
        res = super(ProductTemplate, self)._get_in_production_stock()
        for product in self:
            if product.product_variant_ids:
                self.env.cr.execute(
                    """
                    SELECT pol.id FROM purchase_order_line pol
                    JOIN purchase_order po ON po.id = pol.order_id
                    WHERE pol.state = 'purchase_order' AND po.completed_purchase is False
                    AND pol.company_id = %s AND pol.product_id in %s
                    """, (self.env.user.company_id.id, tuple(product.product_variant_ids.ids))
                )
                qty = self.env.cr.fetchall()
                if qty:
                    line_ids = [x[0] for x in qty]
                    lines = self.env['purchase.order.line'].browse(line_ids)
                    product.qty_in_production += sum(lines.mapped("production_qty"))
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _purchase_count(self):

        domain = [
            ('product_id', 'in', self.ids),
            ('state', 'in', ['purchase', 'done', 'purchase_order'])
        ]

        purchase_order_lines = self.env['purchase.order.line'].read_group(domain,
                                                                          ['product_qty', 'product_id', 'state'],
                                                                          ['product_id', 'state'], lazy=False)

        if purchase_order_lines:
            dicc_qty1 = defaultdict(int)
            dicc_qty2 = defaultdict(int)

            for purchase in purchase_order_lines:
                product = purchase.get('product_id')[0]
                if purchase.get('state') == 'purchase_order':
                    dicc_qty1[product] += purchase.get('product_qty')
                else:
                    dicc_qty2[product] += purchase.get('product_qty')

            for product in self:
                product.split_purchase_count = dicc_qty1.get(product.id) or 0
                product.purchase_count = dicc_qty2.get(product.id) or 0

    purchase_count = fields.Integer(compute='_purchase_count')
    split_purchase_count = fields.Integer(compute='_purchase_count')
