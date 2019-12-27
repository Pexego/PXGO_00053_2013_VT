from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id')
    def onchange_partner_id_purchase_order_line(self):
        for line in self.order_line:
            if line.is_supplier_product:
                self.order_line-=line
        associated_products = self.partner_id.associated_product_ids
        for product in associated_products:
            new_line = {
                'product_id': product.product_id.id,
            }
            new_line = self.order_line.new(new_line)
            new_line.onchange_product_id()
            new_line['price_unit'] = product.price_unit
            new_line['product_qty'] = product.qty
            new_line['discount'] = product.discount
            new_line['is_supplier_product'] = True
            self.order_line += new_line

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_supplier_product = fields.Boolean()
