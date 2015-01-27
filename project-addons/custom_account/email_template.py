# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api
import base64

class EmailTemplate(models.Model):

    _inherit = 'email.template'


    @api.model
    def generate_email_batch(self, template_id, res_ids, fields=None):
        res = super(EmailTemplate,self).generate_email_batch(template_id, res_ids, fields=fields)
        if self.env.context.get('active_model', '') != 'account.invoice':
            return res
        for res_id in res.keys():
            attachments = res[res_id]['attachments']
            invoice = self.env['account.invoice'].browse(res_id)
            if not invoice.attach_picking:
                continue
            for picking in invoice.picking_ids:
                report = self.env.ref('stock.action_report_picking')
                report_service = report.report_name
                result, format = self.env['report'].get_pdf(picking, report_service), 'pdf'

                result = base64.b64encode(result)
                report_name = 'stock.' + picking.name.replace('/', '')
                ext = "." + format
                if not report_name.endswith(ext):
                    report_name += ext
                attachments.append((report_name, result))
            res[res_id]['attachments'] = attachments
        return res
