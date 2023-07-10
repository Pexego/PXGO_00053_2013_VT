from odoo import models, fields


class ConfirmPurchaseConfirmLinesChecker(models.TransientModel):
    _name = 'confirm.purchase.lines.checker'

    purchase_lines_with_no_price = fields.Many2many(
        'purchase.order.line',
        string='Lines with no price',
        domain=[('price_unit', '=', 0)]
    )
    purchase_lines_with_price_variance = fields.Many2many(
        'purchase.order.line',
        string='Product with high price variance',
        domain=[('price_unit', '!=', 0)]
    )
    purchase_id = fields.Many2one('purchase.order', 'Purchase Order')

    def button_continue(self):
        """
        Calls purchase order's button_confirm bypassing checking lines
        """
        self.purchase_id.with_context(bypass_po_check_lines=True).button_confirm()
