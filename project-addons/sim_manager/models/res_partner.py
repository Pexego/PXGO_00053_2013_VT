from odoo import models, fields, _
from odoo.addons.component.core import Component
import requests
import json
from datetime import datetime
import calendar


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sim_serial_ids = fields.One2many('sim.package', 'partner_id')

    def invoice_sim_packages(self, month=None):
        # execute only if come the month or if today is the last day of the month
        if month or datetime.now().day == calendar.monthrange(datetime.now().year, datetime.now().month)[1]:
            # Call web to get the data
            error = ''
            mail_bank_error_message = ''
            web_invoice_endpoint = self.env['ir.config_parameter'].sudo().get_param('web.sim.invoice.endpoint')
            api_key = self.env['ir.config_parameter'].sudo().get_param('web.sim.invoice.endpoint.key')
            c_code = self.env['ir.config_parameter'].sudo().get_param('country_code')
            headers = {'x-api-key': api_key,
                       'Content-Type': 'application/json'}
            if not month:
                month = datetime.now().month
            data = {
                "origin": c_code.lower(),
                "month": month
            }
            # get last day of the month
            if datetime.now().month == 1 and month == 12:
                year = datetime.now().year - 1
            else:
                year = datetime.now().year
            last_day = calendar.monthrange(year, month)[1]  # return the amount of days of that month
            last_day_date = "%i-%i-%i" % (year, month, last_day)

            response = requests.put(web_invoice_endpoint, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                for partner_data in eval(response.text):
                    if partner_data['odooId'] > 0:
                        partner = self.env['res.partner'].browse(partner_data['odooId'])
                        if partner and partner_data['sims'] > 0 \
                                and partner.comercial != 'VISIOTECH' and partner.comercial != 'Prueba España':
                            price_tags = {'M2M0,7euro': 0.7, 'M2M1euro': 1, 'M2M2euro': 2}
                            product_sim = self.env['product.product'].search([('default_code', '=', 'M2M_COMMUNICATION')])
                            product_sms = self.env['product.product'].search([('default_code', '=', 'M2M_COMMUNICATION_EXTRA_SMS')])
                            product_voz = self.env['product.product'].search([('default_code', '=', 'M2M_COMMUNICATION_EXTRA_MINUTE')])
                            company = self.env['res.company'].browse(1)
                            price_unit = 1.5
                            line_account = self.env['account.invoice.line']. \
                                get_invoice_line_account('out_invoice', product_sim, partner.property_account_position_id, company)
                            for tag in price_tags:
                                if tag in [x.name for x in partner.category_id]:
                                    price_unit = price_tags[tag]
                            inv_data = {'type': 'out_invoice', 'partner_id': partner.id, 'journal_id': 1, 'currency_id': 1,
                                        'company_id': 1, 'not_send_email': True, 'date_invoice': last_day_date}
                            invoice = self.env['account.invoice'].create(inv_data)
                            invoice._onchange_partner_id()

                            line_data = {'sequence': 1, 'product_id': product_sim.id, 'name': product_sim.default_code,
                                         'quantity': round(partner_data['sims'], 2), 'discount': 0, 'uom_id': 1, 'price_unit': price_unit,
                                         'account_id': line_account.id, 'invoice_id': invoice.id}
                            line = self.env['account.invoice.line'].create(line_data)
                            line._onchange_product_id()
                            line._onchange_account_id()
                            line.price_unit = price_unit
                            if partner_data['sms'] > 0:
                                line_data_sms = {'sequence': 1, 'product_id': product_sms.id, 'name': product_sms.default_code,
                                                 'quantity': partner_data['sms'], 'discount': 0, 'uom_id': 1, 'price_unit': 0.08,
                                                 'account_id': line_account.id, 'invoice_id': invoice.id}
                                line_sms = self.env['account.invoice.line'].create(line_data_sms)
                                line_sms._onchange_product_id()
                                line_sms._onchange_account_id()
                                line_sms.price_unit = 0.08
                            if partner_data['voice'] > 0:
                                line_data_voz = {'sequence': 1, 'product_id': product_voz.id, 'name': product_voz.default_code,
                                                 'quantity': partner_data['voice'], 'discount': 0, 'uom_id': 1, 'price_unit': 0.15,
                                                 'account_id': line_account.id, 'invoice_id': invoice.id}
                                line_voz = self.env['account.invoice.line'].create(line_data_voz)
                                line_voz._onchange_product_id()
                                line_voz._onchange_account_id()
                                line_voz.price_unit = 0.15
                            invoice.compute_taxes()
                            
                            if partner.property_payment_term_id.with_context({'lang': 'es_ES'}).name in ('Prepago', 'Pago inmediato'):
                                valid_mandate = self.env['account.banking.mandate'].search_count([('partner_id', '=', partner.id), ('state', '=', 'valid')])
                                if valid_mandate > 0:
                                    rd_payment = self.env['account.payment.mode'].search([('name', '=', 'Recibo domiciliado')])
                                    invoice.write({'payment_mode_id': rd_payment.id})
                                else:
                                    mail_bank_error_message += _('Partner %s has not a valid mandate or account. Invoice %s has not been changed. \n') \
                                                              % (partner.name, invoice.number)
                            invoice.action_invoice_open()
                        else:
                            error += 'Partner id %s not found ' % partner_data['odooId']
            else:
                error += 'Response %s with error: %s' % (response.status_code, response.text)

            # Send mail to accounting if there is partners without bank account
            if mail_bank_error_message:
                mail_pool = self.env['mail.mail']
                context = self._context.copy()
                context.pop('default_state', False)
                context['message_warn'] = mail_bank_error_message
                template_id = self.env.ref('sim_manager.email_template_sim_bank_account_error')
                if template_id:
                    mail_id = template_id.with_context(context).send_mail(self.id)
                    if mail_id:
                        mail_id_check = mail_pool.browse(mail_id)
                        mail_id_check.with_context(context).send()


class PartnerListener(Component):
    _inherit = 'partner.event.listener'

    def export_partner_data(self, record):
        super().export_partner_data(record)
        for sim_pkg in record.sim_serial_ids:
            sim_pkg.with_delay(priority=10).notify_sale_web('sold')
