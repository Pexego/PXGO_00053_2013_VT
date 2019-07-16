from odoo import models, fields, api, exceptions, _


class WizardReclassifyMoveLineBalance(models.TransientModel):

    _name = "wizard.reclassify.move.line.balance"

    dst_account_id = fields.Many2one("account.account", "Account dest.",
                                     required=True)
    dst_date = fields.Date("Accounting date", default=fields.Date.today,
                           required=True)
    journal_id = fields.Many2one("account.journal", "Journal",
                                 required=True)

    @api.multi
    def action_reclassify(self):
        if not self.env.context.get('active_ids'):
            raise exceptions.UserError(_("Any entry selected"))
        elif len(self.env.context['active_ids']) > 1:
            raise exceptions.UserError(_("Only can select one entry to "
                                         "reclassify."))

        line = self.env['account.move.line'].\
            with_context(check_move_validity=False).\
            browse(self.env.context['active_ids'][0])
        if (line.matched_debit_ids or line.matched_credit_ids) and \
                line.reconciled:
            raise exceptions.\
                UserError(_("You are trying to reclassify one entry that are "
                            "already reconciled!"))

        move = self.env['account.move'].\
            with_context(check_move_validity=False).\
            create({'journal_id': self.journal_id.id,
                    'date': self.dst_date,
                    'ref': _("Reclassify: ") + (line.name or '/')})
        line.copy({'account_id': self.dst_account_id.id,
                   'move_id': move.id,
                   'date': self.dst_date,
                   'journal_id': self.journal_id.id})
        cancellation_line = line.copy({'debit': line.credit,
                                       'credit': line.debit,
                                       'move_id': move.id,
                                       'date': self.dst_date,
                                       'journal_id': self.journal_id.id,
                                       'amount_currency':
                                       line.amount_currency and
                                       -line.amount_currency or 0.0})
        move.post()
        (line + cancellation_line).auto_reconcile_lines()

        result = self.env.ref('account.action_move_line_form').read()[0]
        result['domain'] = [('id', '=', move.id)]
        return result
