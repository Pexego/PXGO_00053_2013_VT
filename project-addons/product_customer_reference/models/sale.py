from odoo import models, api, fields, exceptions, _
import requests
from PyPDF2 import PdfFileMerger
from io import BytesIO
import base64


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def get_product_tech_pdf(self):
        for sale in self:
            tech_file_url = self.env['ir.config_parameter'].sudo().get_param('web.product.tech.file')
            merger = PdfFileMerger()
            final_file = BytesIO()

            for line in sale.order_line:
                if line.product_id.type == 'product':
                    # get file and append to the big file
                    filename_url = "%s%s_%s.pdf" % (tech_file_url, line.product_id.default_code, self.partner_id.lang.split('_')[1])
                    try:
                        req = requests.get(filename_url)
                        if req.status_code == 200:
                            prod_file = BytesIO(req.content)
                            merger.append(prod_file)
                    except:
                        pass
            merger.write(final_file)
            fname = 'products_datasheet_%s.pdf' % sale.name
            self.env['ir.attachment'].create({
                'name': 'Products Datasheet',
                'res_model': 'sale.order',
                'res_field': False,
                'res_id': sale.id,
                'type': 'binary',
                'datas': base64.b64encode(final_file.getvalue()),
                'datas_fname': fname,

            })
            merger.close()
