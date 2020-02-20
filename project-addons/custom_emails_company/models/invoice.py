from odoo import models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        layout = \
            'account.mail_template_data_notification_email_account_invoice'
        for invoice in self:
            if not invoice.not_send_email and invoice.type in ('out_invoice', 'out_refund'):
                try:
                    template = invoice.env.\
                        ref('account.email_template_edi_invoice')
                except ValueError:
                    template = False

                body_html = invoice.env['mail.template']. \
                    with_context(template._context). \
                    render_template(template.body_html, 'account.invoice',
                                    invoice.id)
                compose = invoice.env['mail.compose.message'].with_context({
                    'mark_invoice_as_sent': True,
                    'default_use_template': 'template',
                    'custom_layout': layout,
                    'default_res_id': invoice.id,
                    'default_model': 'account.invoice',
                    'email_from': template.email_from,
                    'force_email': True,
                    'default_template_id': template.id,
                }).create({'auto_delete': False,
                           'body': body_html,
                           'email_from': template.email_from,
                           'subject':
                               'VISIOTECH - Factura (Ref ' +
                               invoice.number + ')'})
                values = compose. \
                    generate_email_for_composer(template.id,
                                                [invoice.id])[invoice.id]
                Attachment = self.env['ir.attachment']
                attachment_ids = []
                for attach_fname, attach_datas in values.pop('attachments',
                                                             []):
                    data_attach = {
                        'name': attach_fname,
                        'datas': attach_datas,
                        'datas_fname': attach_fname,
                        'res_model': 'mail.compose.message',
                        'res_id': 0,
                        'type': 'binary'
                    }
                    attachment_ids.append(Attachment.create(data_attach).id)
                compose.attachment_ids = [(6, 0, attachment_ids)]
                compose.send_mail_action()
        return res
