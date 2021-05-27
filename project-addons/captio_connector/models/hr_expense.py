from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from datetime import datetime
import requests
import json


class HrExpense(models.Model):

    _inherit = "hr.expense"

    COUNTRY_ACCOUNTS = {
        'España': 'AA025',
        'Italia': 'AA026',
        'Francia': 'AA031',
        'Portugal': 'AA027',
        'Norte Europa': 'AA028',
        'Magreb': 'AA029',
        'DACH': 'AA025'
    }

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

                # Search for the expenses in the report
                # each expense will be an account.move so each movement can have its own date
                filters = '?filters={"Report_Id":"%s"}' % report["Id"]
                response = requests.get('%s/v3.1/Expenses%s' % (url_api, filters),
                                        headers={'Authorization': 'Bearer ' + token,
                                                 'CustomerKey': ckey})
                if response.status_code == 200:
                    resp_exp = json.loads(response.text)
                    if resp_exp:
                        for count, expense in enumerate(resp_exp):
                            exp_vals = []

                            # Create all the necessary data
                            if expense["PaymentMethod"]["Name"] == 'Tarjeta empresa':
                                payment_method = ' TJ '
                                journal = self.env['account.journal'].search([('code', '=', 'PERS')])
                                close_account = user.card_account_id.id,
                            elif expense["PaymentMethod"]["Name"] == 'Efectivo':
                                payment_method = ' EF '
                                journal = self.env['account.journal'].search([('code', '=', 'MISC')])
                                close_account = user.cash_account_id.id,
                            move_name = user.partner_id.name.upper() + payment_method + report["Code"] + \
                                        ' %s/%s ' % (count + 1, len(resp_exp))
                            line_name = user.partner_id.name.upper()
                            aa_code = self.COUNTRY_ACCOUNTS.get(user.team_id.name, 'AA025')
                            analytic_account_id = self.env['account.analytic.account'].search([('code', '=', aa_code)])
                            # if the expense is from another month, put the creation date
                            if int(expense["Date"][5:7]) != datetime.now().month:
                                exp_date = expense["CreationDate"]
                            else:
                                exp_date = expense["Date"]

                            # Create the move
                            move = self.env['account.move'].create({
                                'ref': move_name,
                                'journal_id': journal.id
                            })
                            account = expense["Category"]["Account"]
                            account_id = self.env['account.account'].search([('code', '=', account)])
                            exp_vals.append({'name': line_name,
                                             'move_id': move.id,
                                             'account_id': account_id.id,
                                             'analytic_account_id': analytic_account_id.id,
                                             'date': exp_date,
                                             'debit': expense["FinalAmount"]["Value"],
                                             'credit': 0})

                            exp_vals.append({'name': line_name,
                                             'move_id': move.id,
                                             'account_id': close_account,
                                             'debit': 0,
                                             'credit': expense["FinalAmount"]["Value"]})

                            move.line_ids = [(0, 0, x) for x in exp_vals]
                            move.post()

        company.captio_last_date = datetime.now()
