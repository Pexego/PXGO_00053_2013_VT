# Necesario para el envio del email de forma automatica justo despues de la validación
from odoo import models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def action_invoice_open(self):

        res = super(AccountInvoice, self).action_invoice_open()
        if not self.not_send_email and self.type == 'out_invoice':
            try:
                template = self.env.ref('account.email_template_edi_invoice')
            except ValueError:
                template = False

            body_html = self.env['mail.template'].with_context(template._context).render_template(template.body_html, 'account.invoice', self.id)
            compose = self.env['mail.compose.message'].with_context({
                     'mark_invoice_as_sent': True,
                     'default_use_template': 'template',
                     'custom_layout': 'account.mail_template_data_notification_email_account_invoice',
                     'default_res_id': self.ids[0],
                     'default_model': 'account.invoice',
                     'email_from': template.email_from,
                }).create({
                'default_model': 'account.invoice',
                'default_res_id': self.ids[0],
                'default_template_id': template.id,
                'force_email': True,
                'body': body_html,
                'email_from': template.email_from,
                'subject': 'VISIOTECH - Factura (Ref ' + self.number + ')'
                })

            compose.send_mail_action()
        return res
