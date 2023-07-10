from odoo import models, fields


class ConfirmPurchaseConfirmLinesChecker(models.TransientModel):
    _name = 'confirm.purchase.lines.checker'

    purchase_lines_with_no_price = fields.Many2many(
        'purchase.order.line',
        string='Lines with no price',
        domain=[('price_unit', '=', 0)]  # l.product_qty == 0
    )
    purchase_lines_with_price_variance = fields.Many2many(
        'purchase.order.line',
        string='Product with high price variance',
        domain=[('price_unit', '!=', 0)]  # l.product_qty != 0
    )

    def button_continue(self):
        # TODO: Confirmar po con bypass_po_check_lines
        pass

