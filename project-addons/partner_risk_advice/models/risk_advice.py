# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from datetime import datetime
from dateutil import relativedelta


class RiskAdviceMail(models.Model):

    _name = "partner.risk.advice"

    days_after = fields.Integer("Days from last invoice")
    global_ok = fields.Boolean(
        "Global", default=False,
        help="True: all partners but those with specific advices")
    partner_id = fields.Many2one("res.partner", "Customer")
    template_id = fields.Many2one("mail.template", "Template", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(global_ok, days_after, partner_id)',
         'global_ok, days_after must be unique')
    ]

    @api.model
    def check_partner_risk(self):
        acc_move_line_obj = self.env['account.move.line']
        partner_ids = acc_move_line_obj.\
            read_group([('partner_id', '!=', False),
                        ('full_reconcile_id', '=', False),
                        ('account_id.internal_type', '=', 'receivable')],
                       ["partner_id"],
                       groupby="partner_id")

        res = {}
        partners = self.env['res.partner'].browse(
            x['partner_id'][0] for x in partner_ids)
        for partner in partners.filtered(
                lambda r: r.credit_limit and r.risk_exception):
            accounts = []
            res = False
            break_risk = False

            if partner.property_account_receivable_id:
                accounts.append(partner.property_account_receivable_id.id)

            circualting_acc_ids = self.env["account.account"].\
                search([('circulating', '=', True)])
            if circualting_acc_ids:
                accounts.extend(circualting_acc_ids.ids)

            line_ids = acc_move_line_obj.search([
                ('partner_id', '=', partner.id),
                ('account_id', 'in', accounts),
                ('reconciled', '=', False),
                ('account_id.internal_type', '=', 'receivable')
                ], order="date_maturity asc")

            amount = 0.0
            for line in line_ids:
                amount += line.currency_id and \
                    line.amount_residual_currency or line.amount_residual
                if amount > partner.credit_limit:
                    # rotura de risk
                    res = {
                        'partner': partner.id,
                        'line': line.id,
                        'amount': amount - partner.credit_limit,
                        'date': line.date_maturity or line.move_id.date,
                        'name': line.ref,
                        'currency': line.currency_id and line.currency_id or line.company_id.currency_id
                    }
                    self.send_risk_advice_mail(res)
                    break_risk = True
                    break  # line in line in line_ids

            if break_risk:
                break  # partner in partner_pool

        return res

    def send_risk_advice_mail(self, values):
        partner = self.env['res.partner'].search(
            [('id', '=', values['partner'])])
        mail_pool = self.env['mail.mail']
        mail_ids = self.env['mail.mail']
        date = datetime.strptime(str(values['date']), '%Y-%m-%d')
        today = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d')
        timing = relativedelta.relativedelta(today, date)
        advices = self.env["partner.risk.advice"]
        if partner.risk_advice_ids:
            advices += partner.risk_advice_ids

        advices += self.env['partner.risk.advice'].search(
            [('global_ok', '=', True)])

        for advice in advices:
            if timing.days == advice.days_after:
                template_id = advice.template_id
                advice_id = {'advice': advice.id}

                if not template_id:
                    break

                ctx = dict(self._context)
                ctx.update({
                    'partner_email': partner.email,
                    'partner_id': partner.id,
                    'partner_name': partner.name,
                    'mail_from': self.env.user.company_id.email,
                })
                ctx.update(values)
                ctx.update(advice_id)

                mail_id = template_id.with_context(ctx).send_mail(partner.id)
                mail_ids += mail_pool.browse(mail_id)
                if mail_ids:
                    mail_ids.send()
