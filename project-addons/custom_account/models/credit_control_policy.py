# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class CreditControlPolicy(models.Model):

    _inherit = "credit.control.policy"

    @api.multi
    def _move_lines_domain(self, controlling_date):
        """ Build the default domain for searching move lines """
        res = super()._move_lines_domain(controlling_date)
        res.append(('blocked', '!=', True))
        return res


class CreditControlRun(models.Model):

    _inherit = "credit.control.run"

    @api.model
    def run_credit_control_cron(self):
        cron = self.create({'date': fields.Date.today()})
        cron.generate_credit_lines()


class CreditCommunication(models.TransientModel):
    _inherit = "credit.control.communication"

    @api.model
    def _generate_comm_from_credit_lines(self, lines):
        res = super()._generate_comm_from_credit_lines(lines)
        new_res = self.browse()
        search_date = (fields.Date.from_string(fields.Date.today()) +
                       relativedelta(days=6)).strftime("%Y-%m-%d")
        for comm in res:
            partner = comm.partner_id
            global_balance = partner.credit - partner.debit
            balance = 0.0
            if global_balance >= 5 and not partner.not_send_following_email:
                line_ids = self.env['account.move.line'].\
                    search([('partner_id', '=', partner.id),
                            ('account_id.internal_type', '=', 'receivable'),
                            ('full_reconcile_id', '=', False),
                            ('move_id.state', '!=', 'draft'),
                            ('company_id', '=', comm.company_id.id),
                            ('blocked', '!=', True),
                            '|', ('date_maturity', '=', False),
                            ('date_maturity', '<=', search_date)])
                balance = sum(line_ids.mapped('balance'))
                if balance >= 5:
                    new_res += comm
        return new_res
