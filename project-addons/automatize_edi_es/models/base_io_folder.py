# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BaseIOFolder(models.Model):

    _inherit = "base.io.folder"

    def action_batch_import(self, file_name, file_content):
        if 'UBL-Order' in file_name:
            action = self.env['sale.order.import'].\
                create({'order_file': file_content,
                        'order_filename': file_name,
                        'state': 'import',
                        'doc_type': 'order',
                        'price_source': 'order'}).import_order_button()
            sale = self.env['sale.order'].browse(action['res_id'])
            sale.with_context(bypass_override=True).action_confirm()
            for picking in sale.picking_ids:
                picking.action_done()
        else:
            super().action_batch_import(file_name, file_content)
