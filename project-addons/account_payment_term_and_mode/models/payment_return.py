from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class PaymentReturn(models.Model):

    _inherit = 'payment.return'

    # Override button function
    @api.multi
    def action_confirm(self):
        self.ensure_one()
        # Check for incomplete lines
        if self.line_ids.filtered(lambda x: not x.move_line_ids):
            raise UserError(
                _("You must input all moves references in the payment "
                  "return."))
        invoices_returned = self.env['account.invoice']
        move = {
            'name': '/',
            'ref': _('Return %s') % self.name,
            'journal_id': self.journal_id.id,
            'date': self.date,
            'company_id': self.company_id.id,
            'period_id': (self.period_id.id or self.period_id.with_context(
                company_id=self.company_id.id).find(self.date).id),
        }
        move_id = self.env['account.move'].create(move)
        for return_line in self.line_ids:
            lines2reconcile = return_line.move_line_ids.mapped(
                'reconcile_id.line_id')
            invoices_returned |= self._get_invoices(lines2reconcile)
            for move_line in return_line.move_line_ids:
                move_amount = self._get_move_amount(return_line, move_line)
                move_line2 = move_line.copy(
                    default={
                        'move_id': move_id.id,
                        'debit': move_amount,
                        'name': move['ref'],
                        'credit': 0,
                    })
                lines2reconcile |= move_line2
                move_line2.copy(
                    default={
                        'debit': 0,
                        'credit': move_amount,
                        'account_id':
                            self.journal_id.default_credit_account_id.id,
                    })
                # Break old reconcile
                move_line.reconcile_id.unlink()
            # Make a new one with at least three moves
            lines2reconcile.reconcile_partial()
            return_line.write(
                {'reconcile_id': move_line2.reconcile_partial_id.id})

            # Mark negative line as no-followup
            for line_id in lines2reconcile:
                if line_id.debit - line_id.credit < 0:
                    line_id.blocked = True

        # Mark invoice as payment refused
        invoices_returned.write(self._prepare_invoice_returned_vals())
        move_id.button_validate()
        self.write({'state': 'done', 'move_id': move_id.id})

        return True