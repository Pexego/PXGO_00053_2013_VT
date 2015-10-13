# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from openerp import models
import base64
import os
import logging
import tempfile
from contextlib import closing

_logger = logging.getLogger(__name__)


class Report(models.Model):

    _inherit = "report"

    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None,
                context=None):
        res = super(Report, self).get_pdf(cr, uid, ids, report_name, html=html,
                                          data=data, context=context)
        if report_name == "stock_custom.report_picking_with_attachments":
            attachments = self.pool["ir.attachment"].\
                search(cr, uid, [("res_model", '=', "stock.picking"),
                                 ("res_id", "in", ids),
                                 ("to_print", "=", True)])
            if attachments:
                pdfdatas = [res]
                temporary_files = []
                for attach in self.pool["ir.attachment"].browse(cr, uid,
                                                                attachments):
                    pdf = attach.datas
                    pdf = base64.decodestring(pdf)
                    pdfdatas.append(pdf)
                if pdfdatas:
                    pdfdocuments = []
                    for pdfcontent in pdfdatas:
                        pdfreport_fd, pdfreport_path = tempfile.\
                            mkstemp(suffix='.pdf', prefix='report.tmp.')
                        temporary_files.append(pdfreport_path)
                        with closing(os.fdopen(pdfreport_fd, 'w')) as pdfr:
                            pdfr.write(pdfcontent)
                        pdfdocuments.append(pdfreport_path)
                    entire_report_path = self._merge_pdf(pdfdocuments)
                    temporary_files.append(entire_report_path)

                    with open(entire_report_path, 'rb') as pdfdocument:
                        content = pdfdocument.read()

                    # Manual cleanup of the temporary files
                    for temporary_file in temporary_files:
                        try:
                            os.unlink(temporary_file)
                        except (OSError, IOError):
                            _logger.error('Error when trying to remove '
                                          'file %s' % temporary_file)

                    return content

        return res
