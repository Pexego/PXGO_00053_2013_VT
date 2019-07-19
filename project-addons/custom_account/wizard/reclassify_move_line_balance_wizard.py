from odoo import models, fields, api, exceptions, _


class WizardReclassifyMoveLineBalance(models.TransientModel):

    _name = "wizard.reclassify.move.line.balance"

    dst_account_id = fields.Many2one("account.account", "Account dest.",
                                     required=True)
    dst_date = fields.Date("Accounting date", default=fields.Date.today,
                           required=True)
    journal_id = fields.Many2one("account.journal", "Journal",
                                 required=True)
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)
    selected_amount = fields.Monetary("Selected amount", readonly=True)
    amount = fields.Monetary("Amount to reclassify", required=True)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get('active_id', False):
            line = self.env['account.move.line'].\
                browse(self.env.context['active_id'])
            if line.amount_currency:
                defaults['selected_amount'] = abs(line.amount_currency)
                defaults['amount'] = abs(line.amount_currency)
                defaults['currency_id'] = line.currency_id.id
            else:
                defaults['selected_amount'] = abs(line.balance)
                defaults['amount'] = abs(line.balance)
                defaults['currency_id'] = line.company_currency_id.id
        return defaults

    @api.multi
    def action_reclassify(self):
        if not self.env.context.get('active_ids'):
            raise exceptions.UserError(_("Any entry selected"))
        elif len(self.env.context['active_ids']) > 1:
            raise exceptions.UserError(_("Only can select one entry to "
                                         "reclassify."))
        elif self.amount <= 0.0:
            raise exceptions.\
                UserError(_("Amount to reclassify must be positive"))
        elif round(self.amount, 2) > round(self.selected_amount, 2):
            raise exceptions.UserError(_("Amount to classify cannot be higher "
                                         "than selected amount"))

        line = self.env['account.move.line'].\
            with_context(check_move_validity=False).\
            browse(self.env.context['active_ids'][0])

        if (line.matched_debit_ids or line.matched_credit_ids) and \
                line.reconciled:
            raise exceptions.\
                UserError(_("You are trying to reclassify one entry that are "
                            "already reconciled!"))
        elif not line.debit and not line.credit:
            raise exceptions.UserError(_("The line selected has not amount to "
                                         "reclassify"))
        if line.amount_currency and round(self.selected_amount, 2) != \
                round(self.amount, 2):
            line.move_id.button_cancel()
            sign = line.amount_currency >= 0 and 1 or -1
            rest_amount_currency = sign * \
                (round(abs(line.amount_currency), 2) -
                 round(self.amount, 2))
            vals = {'amount_currency': sign * round(self.amount, 2)}
            if line.credit:
                new_credit = round((self.amount * line.credit) /
                                   abs(line.amount_currency), 2)
                rest_amount = round(line.credit - new_credit, 2)
                field = "credit"
                vals['credit'] = new_credit
            else:
                new_debit = round((self.amount * line.debit) /
                                  abs(line.amount_currency), 2)
                rest_amount = round(line.debit - new_debit, 2)
                field = "debit"
                vals['debit'] = new_debit
            line.write(vals)
            line.copy({field: rest_amount,
                       'amount_currency': rest_amount_currency})
        elif not line.amount_currency and round(self.selected_amount, 2) != \
                round(self.amount, 2):
            line.move_id.button_cancel()
            if line.debit:
                rest_amount = round(line.debit, 2) - round(self.amount, 2)
                vals = {'debit': round(self.amount, 2)}
                field = "debit"
            else:
                rest_amount = round(line.credit, 2) - round(self.amount, 2)
                vals = {'credit': round(self.amount, 2)}
                field = "credit"
            line.write(vals)
            line.copy({field: rest_amount})
        line.move_id.post()
        line.refresh()

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
