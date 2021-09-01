from odoo import models, api, fields


class PrintRecordLabel(models.TransientModel):
    _inherit = 'wizard.print.record.label'

    copies = fields.Integer(string='Copies', default=1)

    def print_label(self):
        super().print_label()
        if self.copies > 1:
            for copy in range(self.copies - 1):
                record_model = self.env.context['active_model']
                for record_id in self.env.context['active_ids']:
                    record = self.env[record_model].browse(record_id)
                    self.label_id.print_label(self.printer_id, record)

