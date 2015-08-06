# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sánchez <kiko@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################



from openerp import fields, models, api, _
from datetime import datetime
from dateutil import relativedelta

class RiskAdviceMail(models.Model):

    _name = "partner.risk.advice"

    days_after= fields.Integer("Days from last invoice")
    global_ok = fields.Boolean ("Global", default = False, help = "True: all partners but those with specific advices")
    partner_id = fields.Many2one("res.partner", "Customer")
    template_id = fields.Many2one("email.template", "Template", required = True)

    _sql_constraints = [
        ('name_uniq', 'unique(global_ok, days_after, partner_id)', 'global_ok, days_after must be unique')
    ]

    @api.model
    def check_partner_risk(self):
        acc_move_line_obj = self.env['account.move.line']
        partners = acc_move_line_obj.\
            read_group([('partner_id', '!=', False),
                        ('reconcile_id', '!=', False)], ["partner_id"],
                       groupby="partner_id")

        res = {}
        for elem in partners:
            partner = self.env['res.partner'].browse(elem['partner_id'][0])
            if not partner.credit_limit or partner.available_risk > 0:
                continue
            accounts = []
            res = False
            break_risk=False

            if partner.property_account_receivable:
                accounts.append( partner.property_account_receivable.id )

            if partner.property_account_payable:
                accounts.append( partner.property_account_payable.id )

            line_ids = acc_move_line_obj.search([
                ('partner_id','=',partner.id),
                ('account_id', 'in', accounts),
                ('reconcile_id','=',False)
                ], order = "date_maturity asc")

            amount = 0.0
            for line in line_ids:

                if line.currency_id:
                    sign = line.amount_currency < 0 and -1 or 1
                else:
                    sign = (line.debit - line.credit) < 0 and -1 or 1
                amount += sign * line.amount_residual

                if amount > partner.credit_limit:
                    #rotura de risk
                    res = {
                        'partner': partner.id,
                        'line': line.id,
                        'amount': partner.credit - partner.debit,
                        'date' : line.date_maturity or line.move_id.date,
                        'name' : line.ref
                    }
                    ok  = self.send_risk_advice_mail (res)
                    break_risk= True
                    break #line in line in line_ids

            if break_risk == True:
                break #partner in partner_pool

        return res


    def send_risk_advice_mail (self, values):
        partner= self.env['res.partner'].search([('id', '=', values['partner'])])
        mail_pool = self.env['mail.mail']
        mail_ids = self.env['mail.mail']
        date = datetime.strptime(str(values['date']), '%Y-%m-%d')
        today = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d')
        timing = relativedelta.relativedelta(today, date)
        advices = self.env["partner.risk.advice"]
        if partner.risk_advice_ids:
            advices += partner.risk_advice_ids

        advices += self.env['partner.risk.advice'].search([('global_ok','=',True)])

        for advice in advices:

            if timing.days == advice.days_after:
                template_id = advice.template_id
                advice_id = {'advice' : advice.id}

                if not template_id:
                    break

                ctx = dict(self._context)
                ctx.update({
                    'partner_email': partner.email,
                    'partner_id': partner.id,
                    'partner_name': partner.name,
                    'mail_from': self.env.user.company_id.email,
                })
                ctx.update (values)
                ctx.update (advice_id)

                mail_id = template_id.with_context(ctx).send_mail(partner.id)
                mail_ids += mail_pool.browse(mail_id)
                if mail_ids:
                    mail_ids.send()
