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

from odoo import models
import base64
import os
import logging
import tempfile
from contextlib import closing
from PyPDF2 import PdfFileWriter, PdfFileReader

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):

    _inherit = "ir.actions.report"

    def _merge_pdf(self, documents):
        """Merge PDF files into one.

        :param documents: list of path of pdf files
        :returns: path of the merged pdf
        """
        writer = PdfFileWriter()
        streams = []
        for document in documents:
            pdfreport = open(document, 'rb')
            streams.append(pdfreport)
            reader = PdfFileReader(pdfreport)
            for page in range(0, reader.getNumPages()):
                writer.addPage(reader.getPage(page))

        merged_file_fd, merged_file_path = tempfile.mkstemp(
            suffix='.html', prefix='report.merged.tmp.')
        with closing(os.fdopen(merged_file_fd, 'wb')) as merged_file:
            writer.write(merged_file)

        for stream in streams:
            stream.close()

        return merged_file_path

    def render_qweb_pdf(self, res_ids=None, data=None):
        res = super().render_qweb_pdf(res_ids, data)
        if self.report_name == "stock_custom.report_picking_with_attachments":
            attachments = self.env["ir.attachment"].search(
                [("res_model", '=', "stock.picking"),
                 ("res_id", "in", res_ids),
                 ("to_print", "=", True)])
            if attachments:
                pick = self.env['stock.picking'].browse(res_ids[0])
                if pick.partner_id and (pick.partner_id.not_print_picking or
                                        pick.partner_id.commercial_partner_id.
                                        not_print_picking):
                    pdfdatas = []
                else:
                    pdfdatas = [res[0]]
                temporary_files = []
                for attach in attachments:
                    pdf = attach.datas
                    pdf = base64.decodestring(pdf)
                    pdfdatas.append(pdf)
                if pdfdatas:
                    pdfdocuments = []
                    for pdfcontent in pdfdatas:
                        pdfreport_fd, pdfreport_path = tempfile.\
                            mkstemp(suffix='.pdf', prefix='report.tmp.')
                        temporary_files.append(pdfreport_path)
                        with closing(os.fdopen(pdfreport_fd, 'wb')) as pdfr:
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

                    return content, 'pdf'

        return res
