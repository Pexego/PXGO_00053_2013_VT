# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models
from odoo.tools import pycompat
import base64


class EmailTemplate(models.Model):

    _inherit = 'mail.template'

    @api.multi
    def generate_email(self, res_ids, fields=None):
        res = super().generate_email(res_ids, fields=fields)
        if self.model_id.model != "account.invoice":
            return res
        multi_mode = True
        if isinstance(res_ids, pycompat.integer_types):
            res_ids = [res_ids]
            multi_mode = False

        for res_id in res_ids:
            invoice = self.env["account.invoice"].browse(res_id)
            if not invoice.attach_picking:
                continue
            attachments_list = multi_mode and res[res_id]['attachments'] or \
                res['attachments']
            for picking in invoice.picking_ids:
                pdf = self.env.\
                    ref('custom_report_link.report_picking_custom_action').\
                    render_qweb_pdf([picking.id])[0]
                pdf = base64.b64encode(pdf)
                report_name = picking.name.replace('/', '')
                ext = ".pdf"
                if not report_name.endswith(ext):
                    report_name += ext
                attachments_list.append((report_name, pdf))
        return res
