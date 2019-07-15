from odoo import models, fields, api, exceptions, _


class WizardReconcilePaymentStatementLine(models.TransientModel):

    _name = "wizard.reconcile.payment.statement.line"

    journal_id = fields.Many2one("account.journal", "Journal", required=True)
    bank_statement_id = fields.Many2one("account.bank.statement",
                                        "Bank statement", required=True)
    bank_statement_line_id = fields.Many2one("account.bank.statement.line",
                                             "Statement line", required=True)
    currency_id = fields.\
        Many2one('res.currency', string='Currency',
                 related="bank_statement_line_id.journal_currency_id")
    amount_selected = fields.Monetary("Active amount",
                                      compute="_get_active_amount")
    statement_line_amount = fields.\
        Monetary("Statement line amount", readonly=True,
                 related="bank_statement_line_id.amount",
                 currency_field="currency_id")

    @api.multi
    @api.depends('bank_statement_line_id')
    def _get_active_amount(self):
        for wzd in self:
            wzd.amount_selected = sum(self.env['bank.payment.line'].
                                      browse(self._context['active_ids']).
                                      mapped('amount_currency'))

    @api.multi
    def action_reconcile(self):
        self.ensure_one()
        if round(self.amount_selected, 2) != \
                round(self.statement_line_amount, 2):
            raise exceptions.UserError(_("Amounts have to be the same"))

        blines = self.env['bank.payment.line'].\
            browse(self._context['active_ids'])
        payment_orders = blines.mapped('order_id')
        if len(payment_orders) > 1:
            raise exceptions.\
                UserError(_("Lines selected of serveral payment orders"))
        payment_dates = set(blines.mapped('date'))
        if len(payment_dates) > 1:
            raise exceptions.\
                UserError(_("Lines selected of serveral payment dates"))

        domain = [('move_id.payment_order_id', '=', blines[0].order_id.id)]
        if blines[0].order_id.payment_mode_id.\
                offsetting_account == 'bank_account':
            domain.extend([('date', '=', blines[0].date),
                           ('account_id', '=',
                            blines[0].order_id.journal_id.
                            default_debit_account_id.id)])
        else:
            domain.extend([('date_maturity', '=', blines[0].date),
                           ('account_id', '=',
                            blines[0].order_id.payment_mode_id.
                            transfer_account_id.id)])

        domain.extend(['|', ('partner_id', '=', False),
                       ('partner_id', 'in', blines.mapped('partner_id').ids)])
        move_ids = self.env['account.move.line'].search(domain)
        counterpart_aml_dicts = []
        for aml in move_ids:
            counterpart_aml_dicts.append({
                'name': aml.name if aml.name != '/' else aml.move_id.name,
                'debit': aml.credit,
                'credit': aml.debit,
                'move_line': aml
            })
        self.bank_statement_line_id.\
            process_reconciliation(
                counterpart_aml_dicts=counterpart_aml_dicts)
