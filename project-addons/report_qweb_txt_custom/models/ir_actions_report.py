from odoo import api, models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _render_qweb_text(self, objs, data=None):
        if not data:
            data = {
                'doc_ids': objs.ids,
                'doc_model': self.model,
                'docs': objs,
                'report_type': 'qweb-txt'
            }
        return self.render_template(self.report_name, data), 'text'

