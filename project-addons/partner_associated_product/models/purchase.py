from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id')
    def onchange_partner_id_purchase_order_line(self):
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
            self.order_line += new_line
