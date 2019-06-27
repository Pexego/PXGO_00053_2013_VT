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
        states={'sale': [('readonly', False)],
                'done': [('readonly', False)]},
        default='by_product'
    )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('order_id.order_invoice_policy')
    def _get_to_invoice_qty(self):
        lines = self.filtered(lambda sol: sol.order_id.state in ['sale', 'done']
                                          and sol.order_id.order_invoice_policy == 'prepaid'
                                          and 'assigned' in sol.move_ids.mapped('state'))
        for line in lines:
            # Allow to invoice only quantity with stock (reserved)
            line.qty_to_invoice = sum(line.move_ids.filtered(lambda mv: mv.state == 'assigned').mapped('product_qty')) \
                                  - (line.qty_invoiced - line.qty_delivered)

        super(SaleOrderLine, self - lines)._get_to_invoice_qty()

