# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class Report(models.Model):
    _inherit = "ir.actions.report"

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        return super(Report, self.with_context(no_embedded_ubl_xml=True)).\
            render_qweb_pdf(res_ids=res_ids, data=data)
