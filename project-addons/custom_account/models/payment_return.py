from odoo import api, models


class PaymentReturn(models.Model):

    _inherit = "payment.return"

    @api.multi
    def action_confirm(self):
        res = super().action_confirm()
        for return_line in self.line_ids:
            for move_line in return_line.move_line_ids:
                move_line.blocked = True

        return res
