from odoo import models, fields, api, _
import pysftp
import io
import base64


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    edi_partner = fields.Boolean(related="partner_id.edi_enabled", readonly=True)
    partner_final_invoicing_id = fields.Many2one('res.partner')

    @api.multi
    def send_via_edi(self):
        for invoice in self:
            edi_msg = self.env['edif.message'].generate_invoice(invoice)
            filename = 'VT-{}.EDI'.format(invoice.number.replace("/", "-"))

            fileb = io.BytesIO()
            fileb.write(edi_msg.encode('latin-1'))
            fileb.seek(0)  # This allows to reads from the start of the stream

            ftp_dir = self.env['ir.config_parameter'].sudo().get_param('ftp_edi_dir')
            ftp_user = self.env['ir.config_parameter'].sudo().get_param('ftp_edi_user')
            ftp_pass = self.env['ir.config_parameter'].sudo().get_param('ftp_edi_pass')
            ftp_folder_out = self.env['ir.config_parameter'].sudo().get_param('ftp_edi_folder_out')

            # FTP login and place
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            sftp = pysftp.Connection(ftp_dir, username=ftp_user, password=ftp_pass, cnopts=cnopts)
            sftp.chdir(ftp_folder_out)

            try:
                sftp.putfo(fileb, remotepath=ftp_folder_out+filename)
            except:
                self.send_edi_error_mail()

            sftp.close()

            ctx = {}
            self.env['ir.attachment'].with_context(ctx).create({
                'name': filename,
                'res_id': invoice.id,
                'res_model': str(invoice._name),
                'datas': base64.b64encode(fileb.getvalue()),
                'datas_fname': filename,
                'type': 'binary',
            })

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for invoice in self.filtered(lambda i: i.partner_id.commercial_partner_id.edi_enabled):
            if invoice.type == 'out_invoice':
                invoice.send_via_edi()

        return res

    @api.multi
    def send_edi_error_mail(self):
        mail_pool = self.env['mail.mail']
        context = self._context.copy()
        context.pop('default_state', False)

        template_id = self.env.ref('edi_edifact.email_template_edi_send_error')

        if template_id:
            mail_id = template_id.with_context(context).send_mail(self.id)
            if mail_id:
                mail_id_check = mail_pool.browse(mail_id)
                mail_id_check.with_context(context).send()

        return True
