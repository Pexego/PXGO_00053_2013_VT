from odoo import models, fields, api, _
import ftplib


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def send_via_edi(self):
        for invoice in self:
            edi_msg = self.env['edif.message'].generate_invoice(invoice)
            filename = '{}.EDI'.format(invoice.number)

            file = open(filename, 'w')
            file.write(edi_msg)

            ftp_dir = self.env['ir.config_parameter'].sudo().get_param('ftp_edi_dir')
            ftp_user = self.env['ir.config_parameter'].sudo().get_param('ftp_edi_user')
            ftp_pass = self.env['ir.config_parameter'].sudo().get_param('ftp_edi_pass')
            ftp_folder_out = self.env['ir.config_parameter'].sudo().get_param('ftp_edi_folder_out')

            ftp = ftplib.FTP(ftp_dir)
            ftp.login(user=ftp_user, passwd=ftp_pass)
            ftp.cwd(ftp_folder_out)

            f = open(filename, 'rb')
            ftp.storbinary("STOR %s" % filename, f)
