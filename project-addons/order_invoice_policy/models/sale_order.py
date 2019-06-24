from odoo import api, models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_invoice_policy = fields.Selection([
        ('by_product', 'Defined by Product'),
        ('prepaid', 'Before Delivery'),
    ],
        string='Invoicing Policy',
        required=True,
        readonly=True,
        default='by_product'
    )

    @api.multi
    def change_order_invoice_policy(self):
        self.ensure_one()
        if self.order_invoice_policy == 'by_product':
            self.order_invoice_policy = 'prepaid'
            for line in self.order_line:
                line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
        else:
            self.order_invoice_policy = 'by_product'
            for line in self.order_line:
                if line.product_id.invoice_policy != 'order':
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced

