# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, _


class PaymentReturn(models.Model):

    _inherit = "payment.return"

    @api.multi
    def action_confirm(self):
        res = super().action_confirm()
        for return_line in self.line_ids:
            for move_line in return_line.move_line_ids:
                move_line.blocked = True
                # Actualizar referencia de pago del apunte asociado a la(s)
                # factura(s) devueltas con la referencia de la devolución
                move_line.mapped('matched_debit_ids.origin_returned_move_ids').write({'ref_line': self.name})

        return res


class PaymentReturnLine(models.Model):
    _inherit = "payment.return.line"

    @api.multi
    def match_move_lines(self):
        for line in self:
            domain = line.partner_id and [
                ('partner_id', '=', line.partner_id.id)] or []
            domain.extend([
                ('account_id.internal_type', '=', 'receivable'),
                ('reconciled', '=', True),
                '|',
                ('name', 'like', line.reference),
                ('ref', 'like', line.reference),
            ])
            move_lines = self.env['account.move.line'].search(domain)
            if move_lines:
                line.move_line_ids = move_lines.ids
                if not line.concept:
                    line.concept = (_('Move lines: %s') %
                                    ', '.join(move_lines.mapped('name')))
