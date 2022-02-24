from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    @api.multi
    def name_get(self):
        res_list = []
        for line in self:
            res_tuple = (line['id'], line['create_date'])
            res_list.append(res_tuple)
        return res_list


class AccountBankStatementLine(models.Model):

    _inherit = "account.bank.statement.line"

    old_statement_id = fields.Many2one('account.bank.statement', string='Old Statement', index=True, ondelete='cascade')
    old_journal_id = fields.Many2one('account.journal', related='old_statement_id.journal_id', string='Old Journal', store=True, readonly=True)
    ignored_reason = fields.Text("Reason")
    statement_id = fields.Many2one(required=False)

    @api.multi
    def action_launch_ignore(self):
        return {
            'name': _('Ignore Statement Line'),
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'ignore.statement.line.wzd',
            'src_model': 'account.bank.statement.line',
            'type': 'ir.actions.act_window',
            'id': 'ignore_statement_line_wdz_view',
            }

    @api.multi
    def action_ignore(self, reason):
        for line in self:
            bank_statement = line.statement_id
            line.old_statement_id = line.statement_id.id
            line.statement_id = False
            line.ignored_reason = reason
            bank_statement.balance_end_real -= line.amount

    @api.multi
    def action_unignore(self):
        for line in self:
            if line.old_statement_id:
                line.statement_id = line.old_statement_id
                line.old_statement_id = None
                line.statement_id.balance_end_real += line.amount
            else:
                raise UserError(_('There is no old statement to link'))
    
    @api.multi
    def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
        counterpart_aml_dicts = counterpart_aml_dicts or []

        reconciled_accounts = {}

        import ipdb
        ipdb.set_trace()
        for aml_dict in counterpart_aml_dicts:
            if aml_dict['move_line'].reconciled:
                reconciled_accounts['Partner'].append(aml_dict['move_line'].partner_id.name)
                reconciled_accounts['Invoice'].append(str(aml_dict['move_line'].invoice_id.number))
                reconciled_accounts['Amount'].append(str(aml_dict['move_line'].amount_residual)+'€')

        if reconciled_accounts:
            partner_msg, invoice_msg, amount_msg = "", "", ""
            if reconciled_accounts['Partner']:
                partner_msg = ' | '. join(reconciled_accounts['Partner'])
            if reconciled_accounts['Invoice']:
                invoice_msg = ' | '. join(reconciled_accounts['Invoice'])
            if reconciled_accounts['Amount']:
                amount_msg = ' | '. join(reconciled_accounts['Amount'])
            
            raise UserError(_('A selected move line was already reconciled.\n - Partners: %s\n - Invoices: %s\n - Amounts: %s')%
            (partner_msg, invoice_msg, amount_msg))
        super(AccountBankStatementLine, self).process_reconciliation(counterpart_aml_dicts, payment_aml_rec, new_aml_dicts)
