# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
import operator as py_operator


OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne,
    '<>': py_operator.ne
}


class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.multi
    def _get_unreconciled_move_lines(self):
        """ Return unreconciled account move lines related to a partner """
        move_line_obj = self.env['account.move.line']
        move_lines = move_line_obj. \
            search([('partner_id', '=', self.id),
                    ('account_id.internal_type', '=', 'receivable'),
                    ('reconciled', '=', False),
                    ('move_id.state', '!=', 'draft'),
                    '|', ('debit', '>', 0), ('credit', '>', 0)])
        return move_lines

    @api.multi
    def _get_amounts_and_date(self):
        current_date = fields.Date.today()
        for partner in self:
            worst_due_date = False
            amount_due = amount_overdue = 0.0
            unreconciled_aml = partner._get_unreconciled_move_lines()
            for aml in unreconciled_aml:
                date_maturity = aml.date_maturity or aml.date
                if not worst_due_date or date_maturity < worst_due_date:
                    worst_due_date = date_maturity
                amount_due += aml.amount_residual
                if date_maturity <= current_date:
                    amount_overdue += aml.amount_residual

            partner.payment_amount_overdue = amount_overdue
            partner.payment_earliest_due_date = worst_due_date
            partner.payment_amount_due = amount_due

    def _search_amount_due(self, operator, operand):
        partners_data = self.env['account.move.line'].\
            read_group([('account_id.internal_type', '=', 'receivable'),
                        ('reconciled', '=', False),
                        ('partner_id', '!=', False),
                        ('move_id.state', '!=', 'draft'),
                        '|', ('debit', '>', 0), ('credit', '>', 0)],
                       ['partner_id', 'balance'], ['partner_id'])
        valid_partner_ids = []
        for partner_data in partners_data:
            if OPERATORS[operator](partner_data['balance'], operand):
                valid_partner_ids.append(partner_data['partner_id'][0])
        return [('id', 'in', valid_partner_ids)]

    @api.multi
    def _communications_count(self):
        communications_obj = self.env['credit.control.communication']
        for partner in self:
            partner.communications_count = communications_obj.\
                search_count([('partner_id', 'child_of', [partner.id])])

    communications_count = fields.Integer(string="Communication",
                                          compute='_communications_count')

    payment_amount_due = fields.Float(compute='_get_amounts_and_date',
                                      string="Amount Due", readonly=True,
                                      search="_search_amount_due")
    payment_amount_overdue = fields.Float(compute='_get_amounts_and_date',
                                          string="Amount Overdue",
                                          readonly=True)
    payment_earliest_due_date = fields.Date(compute='_get_amounts_and_date',
                                            string="Worst Due Date",
                                            readonly=True)
    latest_followup_level_id = fields.Many2one('credit.control.policy.level',
                                               "Latest Follow-up Level",
                                               readonly=True)
