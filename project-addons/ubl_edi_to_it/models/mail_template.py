# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models
from odoo.tools import pycompat


class MailTemplate(models.Model):

    _inherit = 'mail.template'

    @api.multi
    def generate_email(self, res_ids, fields=None):
        old_res_id = res_ids
        if self.model_id.model == "account.invoice":
            multi_mode = True
            if isinstance(res_ids, pycompat.integer_types):
                res_ids = [res_ids]
                multi_mode = False
            invoice = self.env["account.invoice"].browse(res_ids[0])
            if invoice.commercial_partner_id.attach_ubl_xml_file:
                res = super(MailTemplate, self.
                            with_context(attach_ubl_xml_file=True)).\
                    generate_email(res_ids, fields=fields)
                new_attachments = []
                for attach in res[invoice.id]['attachments']:
                    if attach[0].endswith('.xml'):
                        new_attachments.append(attach)
                if new_attachments:
                    res[invoice.id]['attachments'] = new_attachments
                if not multi_mode:
                    res = res[invoice.id]
                return res
        return super().generate_email(old_res_id, fields=fields)
