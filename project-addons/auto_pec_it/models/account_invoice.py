from odoo import models, fields, api, _
from odoo.addons.queue_job.job import job
from datetime import datetime, timedelta


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    auto_fatturapa_error = fields.Text(
        string='Automatic E-invoice Error'
    )
    invoice_pec_jobs_ids = fields.Many2many(
            comodel_name='queue.job', column1='invoice_id', column2='job_id',
            string="Connector Jobs", copy=False,
        )

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for invoice in self.filtered('electronic_invoice_subjected'):
            if not invoice.fatturapa_state:
                eta = datetime.now() + timedelta(seconds=self.company_id.pec_delay_time * 3600)
                queue_obj = self.env['queue.job'].sudo()
                new_delay = invoice.sudo().with_delay(eta=eta).process_invoice_for_pec_send()  # TODO: cambiar el eta al que sea
                job = queue_obj.search([('uuid', '=', new_delay.uuid)], limit=1)
                invoice.sudo().invoice_pec_jobs_ids |= job
            else:
                invoice.auto_fatturapa_error = 'Attachment already done'
        return res

    @job(default_channel='root.invoice_validate_pec')
    @api.multi
    def process_invoice_for_pec_send(self):
        context = {
            'active_ids': self.id,
        }
        wiz_fattura = self.env["wizard.export.fatturapa"].with_context(context).create({
            "report_print_menu": self.company_id.auto_pec_template.id
        })
        try:
            wiz_fattura.exportFatturaPA()
            attachment = self.fatturapa_attachment_out_id
            if attachment:
                attachment.send_via_pec()
        except Exception as err:
            self.auto_fatturapa_error = '%s' % err



