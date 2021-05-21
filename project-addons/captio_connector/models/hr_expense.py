from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from datetime import datetime
import requests
import json


class HrExpense(models.Model):

    _inherit = "hr.expense"

    @api.model
    def get_new_token_captio(self):

        client_id = self.env['ir.config_parameter'].sudo().get_param('captio.client_id')
        client_secret = self.env['ir.config_parameter'].sudo().get_param('captio.client_secret')
        url_token = self.env['ir.config_parameter'].sudo().get_param('captio.api_token')

        data = 'grant_type=client_credentials&scope=integrations_api&client_id=%s&client_secret=%s' % \
               (client_id, client_secret)
        response = requests.post(url_token, data=data)

        if response.status_code == 200:
            resp = json.loads(response.text)
            self.env.user.company_id.captio_token = resp['access_token']
            self.env.user.company_id.captio_token_expire = datetime.now() + \
                                                           relativedelta(seconds=resp['expires_in'])

    @api.model
    def assign_user_from_captio(self, captio_id):

        token = self.env.user.company_id.captio_token
        ckey = self.env['ir.config_parameter'].sudo().get_param('captio.customer_key')
        url_api = self.env['ir.config_parameter'].sudo().get_param('captio.api_endpoint')
        filters = '?filters={"Id":"%s"}' % captio_id

        response = requests.get('%s/v3.1/Users%s' % (url_api, filters),
                                headers={'Authorization': 'Bearer ' + token,
                                         'CustomerKey': ckey})
        if response.status_code == 200:
            resp = json.loads(response.text)
            user = self.env['res.users'].search([('login', '=', resp[0]["Email"])])
            if user:
                user.captio_id = captio_id
                return user

    @api.model
    def cron_import_captio_expenses(self):

        company = self.env.user.company_id
        url_api = self.env['ir.config_parameter'].sudo().get_param('captio.api_endpoint')

        if not company.captio_token_expire or \
                company.captio_token_expire < datetime.now().strftime('%Y-%m-%d %H:%M:%S'):
            # TODO: revisar si es mejor pasar el captio_token_expire a tipo datetime en vez del now a string
            self.get_new_token_captio()

        token = company.captio_token
        ckey = self.env['ir.config_parameter'].sudo().get_param('captio.customer_key')

        # Search for the reports with status 4 (Approved), and aproved after the last time we check
        filters = '?filters={"Status":"4",“StatusDate”:”>%s”}' % (company.captio_last_date.replace(" ", "T") + "Z")
        response = requests.get('%s/v3.1/Reports%s' % (url_api, filters),
                                headers={'Authorization': 'Bearer ' + token,
                                         'CustomerKey': ckey})
        if response.status_code == 200:
            resp_repo = json.loads(response.text)

            for report in resp_repo:
                user = self.env['res.users'].search([('captio_id', '=', report["User"]["Id"])])
                if not user:
                    user = self.assign_user_from_captio(report["User"]["Id"])

                # Make two calls, one for the credit card and another for cash
                # Each of one will make a separate account_move
                filters = '?filters={"Report_Id":"%s","PaymentMethod_Name":"Tarjeta"}' % report["Id"]
                response = requests.get('%s/v3.1/Expenses%s' % (url_api, filters),
                                        headers={'Authorization': 'Bearer ' + token,
                                                 'CustomerKey': ckey})
                if response.status_code == 200:
                    resp_exp = json.loads(response.text)
                    exp_vals = {}
                    if resp_exp:
                        name = user.partner_id.name.upper() + " TJ " + report["Code"]
                        journal = self.env['account.journal'].search([('code', '=', 'PERS')])
                        analytic_account_id = self.env['account.analytic.account'].search([('code', '=', 'AA025')])
                        move = self.env['account.move'].create({
                            'ref': name,
                            'journal_id': journal.id
                        })
                        total_report = 0
                        for expense in resp_exp:
                            account = expense["Category"]["Account"]
                            account_id = self.env['account.account'].search([('code', '=', account)])
                            if account in exp_vals:
                                exp_vals[account]["debit"] += expense["FinalAmount"]["Value"]
                            else:
                                exp_vals[account] = {'name': name,
                                                     'move_id': move.id,
                                                     'account_id': account_id.id,
                                                     'analytic_account_id': analytic_account_id.id,
                                                     'debit': expense["FinalAmount"]["Value"],
                                                     'credit': 0}
                            total_report += expense["FinalAmount"]["Value"]

                        exp_vals[int(user.card_account_id.code)] = {'name': name,
                                                                    'move_id': move.id,
                                                                    'account_id': user.card_account_id.id,
                                                                    'debit': 0,
                                                                    'credit': total_report}

                        move.line_ids = [(0, 0, x) for x in exp_vals.values()]
                        move.post()

                filters = '?filters={"Report_Id":"%s","PaymentMethod_Name":"Efectivo"}' % report["Id"]
                response = requests.get('%s/v3.1/Expenses%s' % (url_api, filters),
                                        headers={'Authorization': 'Bearer ' + token,
                                                 'CustomerKey': ckey})
                if response.status_code == 200:
                    resp_exp = json.loads(response.text)
                    exp_vals = {}
                    if resp_exp:
                        name = user.partner_id.name.upper() + " EF " + report["Code"]
                        journal = self.env['account.journal'].search([('code', '=', 'MISC')])
                        analytic_account_id = self.env['account.analytic.account'].search([('code', '=', 'AA025')])
                        move = self.env['account.move'].create({
                            'ref': name,
                            'journal_id': journal.id
                        })
                        total_report = 0
                        for expense in resp_exp:
                            account = expense["Category"]["Account"]
                            account_id = self.env['account.account'].search([('code', '=', account)])
                            if account in exp_vals:
                                exp_vals[account]["debit"] += expense["FinalAmount"]["Value"]
                            else:
                                exp_vals[account] = {'name': name,
                                                     'move_id': move.id,
                                                     'account_id': account_id.id,
                                                     'analytic_account_id': analytic_account_id.id,
                                                     'debit': expense["FinalAmount"]["Value"],
                                                     'credit': 0}
                            total_report += expense["FinalAmount"]["Value"]

                        exp_vals[int(user.card_account_id.code)] = {'name': name,
                                                                    'move_id': move.id,
                                                                    'account_id': user.cash_account_id.id,
                                                                    'debit': 0,
                                                                    'credit': total_report}

                        move.line_ids = [(0, 0, x) for x in exp_vals.values()]
                        move.post()

        company.captio_last_date = datetime.now()

