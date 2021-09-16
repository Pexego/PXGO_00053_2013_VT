from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        lines = self.env['sale.order.line']
        for order in self:
            promo_lines = order.mapped('order_line').filtered(lambda x: x.original_line_id_promo)
            for line in promo_lines:
                original_line_id_promo = self.env['sale.order.line'].browse(line.original_line_id_promo)
                # For example in 4x3 promo, line.promo_qty_split is equals to 4
                # because this field show us the minimum qty of product for which the promo is applied
                if original_line_id_promo and line.qty_to_invoice != 0:
                    qty_to_invoice = (original_line_id_promo.qty_invoiced +
                                      original_line_id_promo.qty_to_invoice)//line.promo_qty_split - line.qty_invoiced
                    line.qty_to_invoice = qty_to_invoice
                    if qty_to_invoice == 0:
                        lines += line
        res = super(SaleOrder, self).action_invoice_create(grouped=grouped, final=final)
        for line in lines:
            if line.product_uom_qty != line.qty_invoiced:
                line.qty_to_invoice = line.product_uom_qty-line.qty_invoiced
        return res
