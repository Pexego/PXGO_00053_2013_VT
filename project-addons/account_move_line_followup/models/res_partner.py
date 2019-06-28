# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _


class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.multi
    def _get_unreconciled_move_lines(self):
        """ Return unreconciled account move lines related to a partner """
        move_line_obj = self.env['account.move.line']
        move_lines = move_line_obj. \
            search([('partner_id', '=', self.id),
                    ('account_id.internal_type', '=', 'receivable'),
                    ('full_reconcile_id', '=', False),
                    ('move_id.state', '!=', 'draft')])
        return move_lines

    @api.multi
    def _get_amounts_and_date(self):
        company = self.env['res.users'].browse([self.env.uid]).company_id
        current_date = fields.Date.today()
        for partner in self:
            worst_due_date = False
            amount_due = amount_overdue = 0.0
            unreconciled_aml = partner._get_unreconciled_move_lines()
            for aml in unreconciled_aml:
                if aml.company_id == company:
                    date_maturity = aml.date_maturity or aml.date
                    if not worst_due_date or date_maturity < worst_due_date:
                        worst_due_date = date_maturity
                    amount_due += aml.balance
                    if date_maturity <= current_date:
                        amount_overdue += aml.balance

            partner.payment_amount_due = amount_due
            partner.payment_amount_overdue = amount_overdue
            partner.payment_earliest_due_date = worst_due_date

    @api.multi
    def _communications_count(self):
        communications_obj = self.env['credit.control.communication']
        for partner in self:
            partner.communications_count = communications_obj.search_count([('partner_id', 'child_of', [partner.id])])

    communications_count = fields.Integer(string="Communication", compute='_communications_count')

    payment_amount_due = fields.Float(compute='_get_amounts_and_date', string="Amount Due", store=True, readonly=True)
    payment_amount_overdue = fields.Float(compute='_get_amounts_and_date', string="Amount Overdue", readonly=True)
    payment_earliest_due_date = fields.Date(compute='_get_amounts_and_date', string="Worst Due Date", readonly=True)
    latest_followup_level_id = fields.Many2one('credit.control.policy.level', "Latest Follow-up Level", readonly=True)

