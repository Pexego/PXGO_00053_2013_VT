# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta


class CreditControlPolicy(models.Model):

    _inherit = "credit.control.policy"

    @api.multi
    def _move_lines_domain(self, controlling_date):
        """ Build the default domain for searching move lines """
        res = super()._move_lines_domain(controlling_date)
        res.append(('blocked', '!=', True))
        return res


class CreditControlPolicyLine(models.Model):

    _inherit = "credit.control.policy.level"

    channel = fields.Selection(selection_add=[('manual_action', 'Manual Action')])


class CreditControlLine(models.Model):

    _inherit = "credit.control.line"

    channel = fields.Selection(selection_add=[('manual_action', 'Manual Action')])

    @api.model
    def create(self, vals):
        if vals.get('channel', False) and vals['channel'] == 'manual_management':
            vals.update({'manual_followup': True})
        return super().create(vals)


class CreditControlRun(models.Model):

    _inherit = "credit.control.run"

    @api.model
    def run_credit_control_cron(self):
        cron = self.create({'date': fields.Date.today()})
        cron.generate_credit_lines()
        cron.set_to_ready_lines()
        cron.run_channel_action()


class CreditCommunication(models.TransientModel):
    _inherit = "credit.control.communication"

    move_line_ids = fields.Many2many('account.move.line', rel='comm_aml_rel', string="Account Move Lines")

    @api.model
    @api.returns('account.move.line')
    def _get_unreconciled_move_lines(self):
        """ Return unreconciled account move lines related to a partner """
        search_date = (fields.Date.from_string(fields.Date.today()) +
                       relativedelta(days=6)).strftime("%Y-%m-%d")
        move_line_obj = self.env['account.move.line']
        move_lines = move_line_obj.\
            search([('partner_id', '=', self.partner_id.id),
                    ('account_id.internal_type', '=', 'receivable'),
                    ('full_reconcile_id', '=', False),
                    ('move_id.state', '!=', 'draft'),
                    ('company_id', '=', self.company_id.id),
                    ('blocked', '!=', True),
                    '|', ('date_maturity', '=', False),
                    ('date_maturity', '<=', search_date)])
        return move_lines

    @api.model
    def _generate_comm_from_credit_lines(self, lines, days_delay=6):
        comms = super()._generate_comm_from_credit_lines(lines)

        new_comms = self.browse()
        partner_obj = self.env['res.partner']
        policy_level_obj = self.env['credit.control.policy.level']

        sql = (
            """ SELECT ccl.partner_id, max(ccl.level) as level, ccl.policy_id, ccl.currency_id
                FROM credit_control_line ccl
                JOIN credit_control_policy_level ccpl ON ccpl.id = ccl.policy_level_id
                JOIN account_move_line aml ON aml.id = ccl.move_line_id
                WHERE ccl.id in %s AND COALESCE(aml.full_reconcile_id, 0) = 0 
                GROUP BY ccl.partner_id, ccl.policy_id, ccl.currency_id

        """)
        cr = self.env.cr
        cr.execute(sql, (tuple(lines.ids), ))
        res = cr.dictfetchall()
        company_currency = self.env.user.company_id.currency_id

        for group in res:
            data = {}
            partner = partner_obj.browse([group['partner_id']])
            global_balance = partner.credit - partner.debit
            if global_balance >= 5 and not partner.not_send_following_email:

                partner_policy_level = policy_level_obj.search_read([('policy_id', '=', group['policy_id']),
                                                                     ('level', '=', group['level'])],
                                                                    ['id'], limit=1)
                data['partner_id'] = group['partner_id']
                data['current_policy_level'] = partner_policy_level[0]['id']
                data['currency_id'] = group['currency_id'] or company_currency.id
                comm = self.create(data)

                move_lines = comm._get_unreconciled_move_lines()

                balance = sum(move_lines.mapped('balance'))
                if balance >= 5:
                    data['move_line_ids'] = [(6, 0, move_lines.ids)]
                    comm.write(data)
                    new_comms += comm
        return new_comms

    @api.multi
    def get_followup_table_html_base(self, moves):
        partner = self.partner_id.commercial_partner_id
        context = dict(self.env.context, lang=partner.lang)
        currency = self.company_id.currency_id
        followup_table = ''
        total = 0.0

        if moves:
            followup_table = '''
                  <table border="2" width=100%%>
                  <tr>
                      <td>''' + _("Invoice Date") + '''</td>
                      <td>''' + _("Invoice No.") + '''</td>
                      <td>''' + _("Due Date") + '''</td>
                      <td>''' + _("Amount") + " (%s)" % currency.symbol + '''</td>
                  </tr>
                  '''
            for aml in moves:
                total += aml['balance']
                strbegin = "<TD>"
                strend = "</TD>"
                date = aml['date_maturity'] or aml['date']
                followup_table += "<TR>" + strbegin + str(aml['date']) + strend + \
                                  strbegin + (aml['ref'] or '') + strend + \
                                  strbegin + str(date) + strend + strbegin + \
                                  str(aml['balance']) + strend + "</TR>"

        return followup_table, total

    @api.multi
    def get_followup_table_html_not_due(self):
        today = fields.Date.from_string(fields.Date.today()).strftime("%Y-%m-%d")
        aml_ids = self.move_line_ids
        aml_not_due = aml_ids.filtered(lambda l: today < l.date_maturity)
        followup_table, total = self.get_followup_table_html_base(aml_not_due)
        if followup_table:
            followup_table += '''<tr> </tr>
                                       </table>
                                       <strong><center style="font-size: 18px">''' + _("Amount not due") + \
                              ''' : %s </center></strong>''' % (round(total, 2))
        return followup_table

    @api.multi
    def get_followup_table_html_due(self):
        today = fields.Date.from_string(fields.Date.today()).strftime("%Y-%m-%d")
        aml_ids = self.move_line_ids
        aml_due = aml_ids.filtered(lambda l: today >= l.date_maturity)
        followup_table, total = self.get_followup_table_html_base(aml_due)
        if followup_table:
            followup_table += '''<tr> </tr>
                                       </table>
                                       <strong><center style="font-size: 18px">''' + _("Amount due") + \
                              ''' : %s </center></strong>''' % (round(total, 2))
        return followup_table
