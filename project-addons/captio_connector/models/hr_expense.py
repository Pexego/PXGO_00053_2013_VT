from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar
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
        country_code = self.env['ir.config_parameter'].sudo().get_param('country_code')
        url_api = self.env['ir.config_parameter'].sudo().get_param('captio.api_endpoint')

        if not company.captio_token_expire or \
                company.captio_token_expire < datetime.now().strftime('%Y-%m-%d %H:%M:%S'):
            # TODO: revisar si es mejor pasar el captio_token_expire a tipo datetime en vez del now a string
            self.get_new_token_captio()

        token = company.captio_token
        ckey = self.env['ir.config_parameter'].sudo().get_param('captio.customer_key')

        # Search for the reports with status 4 (Approved), and aproved after the last time we check
        filters = '?filters={"Status":"4","StatusDate":">%s"}' % (company.captio_last_date.replace(" ", "T") + "Z")
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
                            if expense["PaymentMethod"]["Name"] in ('Tarjeta empresa', 'Carta di credito', 'Carte Crédit'):
                                payment_method = ' TJ '
                                journal = self.env['account.journal'].search([('expenses_journal', '=', True)])
                                close_account = user.card_account_id.id,
                            elif expense["PaymentMethod"]["Name"] in ('Efectivo', 'Contanti', 'En espèces'):
                                payment_method = ' EF '
                                journal = self.env['account.journal'].search([('expenses_journal', '=', True)])
                                close_account = user.cash_account_id.id,
                            move_name = user.partner_id.name.upper() + payment_method + report["Code"] + \
                                        ' %s/%s ' % (count + 1, len(resp_exp))
                            line_name = user.partner_id.name.upper()
                            analytic_account_id = user.analytic_account_id.id if user.analytic_account_id else False
                            # if the expense is not from the past month or the current one, put the last day of the past month
                            if int(expense["Date"][5:7]) == datetime.now().month \
                                    or int(expense["Date"][5:7]) == (datetime.now() - timedelta(days=30)).month:
                                exp_date = expense["Date"]
                            else:
                                # This gets the last day of the past month
                                exp_date_year = (datetime.now() - timedelta(days=30)).year
                                exp_date_month = (datetime.now() - timedelta(days=30)).month
                                exp_date_day = calendar.monthrange(exp_date_year, exp_date_month)[1]
                                exp_date = "%i-%i-%i" % (exp_date_year, exp_date_month, exp_date_day)

                            # Create the move
                            move = self.env['account.move'].create({
                                'ref': move_name,
                                'journal_id': journal.id
                            })
                            account = expense["Category"]["Account"]
                            account_id = self.env['account.account'].search([('code', '=', account),
                                                                             ('company_id', '=', self.env.user.company_id.id)])
                            partner_id = None
                            if expense["CustomFields"] and country_code == 'IT':
                                if 5480 in [cf['Id'] for cf in expense["CustomFields"]]:
                                    # 5480 id of the field 'fattura' in Captio Italy
                                    i_field = [cf['Id'] for cf in expense["CustomFields"]].index(5480)
                                    if eval(expense["CustomFields"][i_field]["Value"].capitalize()):
                                        # Italy Supplier Account
                                        account_id = self.env['account.account'].search([('code', '=', '250100')])
                                        if expense["Merchant"]:
                                            array_partner = expense["Merchant"].split(' ')
                                            del array_partner[-1]
                                            partial_name = " ".join(array_partner)
                                            partner_id = self.env['res.partner'].search(
                                                [('name', 'ilike', partial_name),
                                                 ('supplier', '=', True)], limit=1)

                            exp_vals.append({'name': line_name,
                                             'move_id': move.id,
                                             'account_id': account_id.id,
                                             'analytic_account_id': analytic_account_id,
                                             'date': exp_date,
                                             'debit': expense["FinalAmount"]["Value"],
                                             'credit': 0,
                                             'partner_id': partner_id or None})

                            exp_vals.append({'name': line_name,
                                             'move_id': move.id,
                                             'account_id': close_account,
                                             'debit': 0,
                                             'credit': expense["FinalAmount"]["Value"]})

                            move.line_ids = [(0, 0, x) for x in exp_vals]
                            move.move_type = 'other'
                            move.post()

        company.captio_last_date = datetime.now()

    @api.model
    def cron_import_captio_expenses_invoice(self):
        company = self.env.user.company_id
        url_api = self.env['ir.config_parameter'].sudo().get_param('captio.api_endpoint')

        # -- Token Captio --
        if not company.captio_token_expire or \
                company.captio_token_expire < datetime.now().strftime('%Y-%m-%d %H:%M:%S'):
            # TODO: revisar si es mejor pasar el captio_token_expire a tipo datetime en vez del now a string
            self.get_new_token_captio()
        token = company.captio_token
        ckey = self.env['ir.config_parameter'].sudo().get_param('captio.customer_key')

        # Search reports with SIIStatus "Pendientes de exportar" after the last time we check
        filters = '?filters={"SIIStatus":"2","SIIStatusDate":">%s"}' \
                  % (company.captio_last_date.replace(" ", "T") + "Z")
        response = requests.get('%s/v3.1/SII%s' % (url_api, filters),
                                headers={'Authorization': 'Bearer ' + token,
                                         'CustomerKey': ckey})
        if response.status_code == 200:
            resp_repo = json.loads(response.text)

            for report in resp_repo:
                for count, sii_expense in enumerate(report["ExpensesSIIData"]):
                    if sii_expense["ApprovalDate"][:10] >= (datetime.now() - relativedelta(days=30)).strftime('%Y-%m-%d'):
                        if sii_expense["InvoiceTypeCode"] == "F1" and sii_expense["SpanishNIF"]:  # Full Invoice
                            # Create full Supplier Invoice
                            # -- Detail of the expense --
                            exp_filters = '?filters={"Id":"%s"}' % sii_expense["ExpenseId"]
                            expense_resp = requests.get('%s/v3.1/Expenses%s' % (url_api, exp_filters),
                                                        headers={'Authorization': 'Bearer ' + token,
                                                                 'CustomerKey': ckey})
                            if expense_resp.status_code == 200:
                                expense_detail = json.loads(expense_resp.text)[0]

                            # -- User --
                            user = self.env['res.users'].search([('captio_id', '=', expense_detail["User"]["Id"])])
                            if not user:
                                user = self.assign_user_from_captio(expense_detail["User"]["Id"])

                            # -- Accounts --
                            l_account = self.env['account.account'].search([('code', '=', expense_detail["Category"]["Account"]),
                                                                            ('company_id', '=',
                                                                              self.env.user.company_id.id)])
                            a_account = user.analytic_account_id.id if user.analytic_account_id else False

                            # -- Supplier --
                            if sii_expense["IssuerTypeID"] == "06":
                                partner_cif = sii_expense["IssuerID"]
                            else:
                                partner_cif = sii_expense["SpanishNIF"]

                            partner = self.env['res.partner'].search([('vat', 'ilike', partner_cif),
                                                                      ('is_company', '=', True),
                                                                      ('supplier', '=', True)])
                            fiscal_position = self.env['account.fiscal.position'].search([('company_id', '=', 1),
                                                                                          ('country_id.code', '=', 'ES')])
                            if not partner:
                                p_vals = {
                                    'name': sii_expense["CompanyName"],
                                    'country_id': self.env['res.country'].search(
                                        [('code', '=', sii_expense["CountryCode"])]).id,
                                    'is_company': True,
                                    'property_account_payable_id':
                                        self.env['account.account'].search([('code', '=', '41000000'),
                                                                            ('company_id', '=', self.env.user.company_id.id)]),
                                    'supplier': True,
                                    'customer': False,
                                    'property_account_position_id': fiscal_position.id,
                                    'vat': 'ES' + partner_cif
                                }
                                partner = self.env['res.partner'].create(p_vals)

                            # -- Create Invoice --
                            journal = self.env['account.journal'].search([('code', '=', 'Servi'), ('company_id', '=', 1)])

                            inv_data = {'type': 'in_invoice',
                                        'journal_id': journal.id,
                                        'partner_id': partner.id,
                                        'reference': sii_expense["InvoiceNumber"],
                                        'date_invoice': sii_expense["IssueDate"],
                                        'currency_id': 1, 'company_id': 1,
                                        'fiscal_position_id': fiscal_position.id,
                                        'captio_img_url': 'http://api-storage.captio.net/api/GetFile?key=' + expense_detail['UrlKey'],
                                        'comment': 'Captio - ' + sii_expense["ExpenseExternalId"]}
                            invoice = self.env['account.invoice'].create(inv_data)
                            for tax_line in sii_expense["VatDetail"]:
                                if tax_line.get("TaxableBase", 0.0):
                                    if float(tax_line.get("TaxableBase", 0.0)) != 0.0:
                                        # -- Taxes --
                                        tax_id = self.env['account.tax'].search([('type_tax_use', '=', 'purchase'),
                                                                                 ('company_id', '=', 1),
                                                                                 ('amount', '=', tax_line["TaxRate"]),
                                                                                 ('description', '=like', '%\_BC'),
                                                                                 ('description', 'not like', '_IC_')])
                                        line_data = {'sequence': 1,
                                                     'name': sii_expense["TransactionDescription"],
                                                     'quantity': 1, 'discount': 0, 'uom_id': 1,
                                                     'price_unit': tax_line["TaxableBase"],
                                                     'account_id': l_account.id,
                                                     'account_analytic_id': a_account if a_account else False,
                                                     'invoice_line_tax_ids': [[6, False, [tax_id[0].id]]],
                                                     'invoice_id': invoice.id}
                                        line = self.env['account.invoice.line'].create(line_data)
                            invoice.compute_taxes()
                            invoice.action_invoice_open()

                            # -- Account Move to pay the invoice -- (like a normal expense but with 410 account)
                            exp_vals = []
                            # Create all the necessary data
                            if expense_detail["PaymentMethod"]["Name"] in ('Tarjeta empresa', 'Carta di credito', 'Carte Crédit'):
                                payment_method = ' TJ '
                                journal = self.env['account.journal'].search([('expenses_journal', '=', True)])
                                close_account = user.card_account_id.id,
                            elif expense_detail["PaymentMethod"]["Name"] in ('Efectivo', 'Contanti', 'En espèces'):
                                payment_method = ' EF '
                                journal = self.env['account.journal'].search([('expenses_journal', '=', True)])
                                close_account = user.cash_account_id.id,
                            if user.name == 'Generica Gastos':
                                filters_report = '?filters={"Id":"%s"}' % report["Id"]
                                response_report = requests.get('%s/v3.1/Reports%s' % (url_api, filters_report),
                                                               headers={'Authorization': 'Bearer ' + token,
                                                                        'CustomerKey': ckey})
                                if response_report.status_code == 200:
                                    report_detail = json.loads(response_report.text)[0]
                                    # It should come just one expense, don't know why it's coming in array form
                                    if report_detail:
                                        move_name = report_detail["Name"] + ' ' + report["ExternalId"] + ' %s/%s ' % (
                                        count + 1, len(report["ExpensesSIIData"]))
                            else:
                                move_name = user.partner_id.name.upper() + payment_method + report["ExternalId"] + \
                                            ' %s/%s ' % (count + 1, len(report["ExpensesSIIData"]))
                            line_name = user.partner_id.name.upper()
                            analytic_account_id = user.analytic_account_id.id if user.analytic_account_id else False
                            # if the expense is not from the past month or the current one, put the last day of the past month
                            if int(expense_detail["Date"][5:7]) == datetime.now().month \
                                    or int(expense_detail["Date"][5:7]) == (datetime.now() - timedelta(days=30)).month:
                                exp_date = expense_detail["Date"]
                            else:
                                # This gets the last day of the past month
                                exp_date_year = (datetime.now() - timedelta(days=30)).year
                                exp_date_month = (datetime.now() - timedelta(days=30)).month
                                exp_date_day = calendar.monthrange(exp_date_year, exp_date_month)[1]
                                exp_date = "%i-%i-%i" % (exp_date_year, exp_date_month, exp_date_day)

                                # Create the move
                            move = self.env['account.move'].create({
                                'ref': move_name,
                                'journal_id': journal.id
                            })
                            account_id = self.env['account.account'].search([('code', '=', '41000000'),
                                                                             ('company_id', '=',
                                                                              self.env.user.company_id.id)])

                            exp_vals.append({'name': line_name,
                                             'move_id': move.id,
                                             'account_id': account_id.id,
                                             'analytic_account_id': analytic_account_id,
                                             'partner_id': partner.id,
                                             'date': exp_date,
                                             'debit': expense_detail["FinalAmount"]["Value"],
                                             'credit': 0})

                            exp_vals.append({'name': line_name,
                                             'move_id': move.id,
                                             'account_id': close_account,
                                             'debit': 0,
                                             'credit': expense_detail["FinalAmount"]["Value"]})

                            move.line_ids = [(0, 0, x) for x in exp_vals]
                            move.move_type = 'other'
                            move.post()

                            # -- Reconcile --
                            moves_to_reconcile = move.line_ids.filtered(lambda l: l.account_id.id == account_id.id)
                            moves_to_reconcile += invoice.move_id.line_ids.filtered(lambda l: l.account_id.id == account_id.id)
                            moves_to_reconcile.reconcile()

                        else:  # Normal Expense
                            # each expense will be an account.move so each movement can have its own date
                            filters = '?filters={"Id":"%s"}' % sii_expense["ExpenseId"]
                            response = requests.get('%s/v3.1/Expenses%s' % (url_api, filters),
                                                    headers={'Authorization': 'Bearer ' + token,
                                                             'CustomerKey': ckey})
                            if response.status_code == 200:
                                expense = json.loads(response.text)[0]
                                # It should come just one expense, don't know why it's coming in array form
                                if expense:
                                    exp_vals = []
                                    user = self.env['res.users'].search([('captio_id', '=', expense["User"]["Id"])])
                                    if not user:
                                        user = self.assign_user_from_captio(expense["User"]["Id"])

                                    # Create all the necessary data
                                    if expense["PaymentMethod"]["Name"] in ('Tarjeta empresa', 'Carta di credito', 'Carte Crédit'):
                                        payment_method = ' TJ '
                                        journal = self.env['account.journal'].search([('expenses_journal', '=', True)])
                                        close_account = user.card_account_id.id,
                                    elif expense["PaymentMethod"]["Name"] in ('Efectivo', 'Contanti', 'En espèces'):
                                        payment_method = ' EF '
                                        journal = self.env['account.journal'].search([('expenses_journal', '=', True)])
                                        close_account = user.cash_account_id.id,
                                    if user.name == 'Generica Gastos':
                                        filters_report = '?filters={"Id":"%s"}' % report["Id"]
                                        response_report = requests.get('%s/v3.1/Reports%s' % (url_api, filters_report),
                                                                headers={'Authorization': 'Bearer ' + token,
                                                                         'CustomerKey': ckey})
                                        if response_report.status_code == 200:
                                            report_detail = json.loads(response_report.text)[0]
                                            # It should come just one expense, don't know why it's coming in array form
                                            if report_detail:
                                                move_name = report_detail["Name"] + ' ' + report["ExternalId"] + ' %s/%s ' % (count + 1, len(report["ExpensesSIIData"]))
                                    else:
                                        move_name = user.partner_id.name.upper() + payment_method + report["ExternalId"] + \
                                                    ' %s/%s ' % (count + 1, len(report["ExpensesSIIData"]))
                                    line_name = user.partner_id.name.upper()
                                    analytic_account_id = user.analytic_account_id.id if user.analytic_account_id else False
                                    # if the expense is not from the past month or the current one, put the last day of the past month
                                    if int(expense["Date"][5:7]) == datetime.now().month \
                                            or int(expense["Date"][5:7]) == (datetime.now() - timedelta(days=30)).month:
                                        exp_date = expense["Date"]
                                    else:
                                        # This gets the last day of the past month
                                        exp_date_year = (datetime.now() - timedelta(days=30)).year
                                        exp_date_month = (datetime.now() - timedelta(days=30)).month
                                        exp_date_day = calendar.monthrange(exp_date_year, exp_date_month)[1]
                                        exp_date = "%i-%i-%i" % (exp_date_year, exp_date_month, exp_date_day)

                                        # Create the move
                                    move = self.env['account.move'].create({
                                        'ref': move_name,
                                        'journal_id': journal.id
                                    })
                                    account = expense["Category"]["Account"]
                                    account_id = self.env['account.account'].search([('code', '=', account),
                                                                                     ('company_id', '=',
                                                                                      self.env.user.company_id.id)])

                                    exp_vals.append({'name': line_name,
                                                     'move_id': move.id,
                                                     'account_id': account_id.id,
                                                     'analytic_account_id': analytic_account_id,
                                                     'date': exp_date,
                                                     'debit': expense["FinalAmount"]["Value"],
                                                     'credit': 0})

                                    exp_vals.append({'name': line_name,
                                                     'move_id': move.id,
                                                     'account_id': close_account,
                                                     'debit': 0,
                                                     'credit': expense["FinalAmount"]["Value"]})

                                    move.line_ids = [(0, 0, x) for x in exp_vals]
                                    move.move_type = 'other'
                                    move.post()

        company.captio_last_date = datetime.now()
