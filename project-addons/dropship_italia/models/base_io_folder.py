from odoo import api, fields, models, _


class BaseIOFolder(models.Model):
    _inherit = "base.io.folder"

    @api.model
    def _scheduler_import_file_dropship(self, max_commit_length=False):
        for config in self.search([('direction', '=', 'dropship')]):
            continue_search = True
            while continue_search:
                imported_files, continue_search = config._iter_directory(max_commit_length)
                self.env.cr.commit()
                for file_imported, file_full_name in imported_files:
                    config._after_import(file_imported, file_full_name)

    def action_batch_import(self, file_name, file_content):
        if 'UBL-D-Order' in file_name:
            action = self.env['sale.order.import']. \
                create({'order_file': file_content,
                        'order_filename': file_name,
                        'state': 'import',
                        'doc_type': 'order',
                        'price_source': 'order'}).with_context(dropship_sale=True).import_order_button()
            sale = self.env['sale.order'].browse(action['res_id'])
            for line in sale.order_line:
                line.route_id = None
                # Delete the route in order to create a normal picking
            sale.not_sync = False
            sale.with_context(bypass_override=True).action_confirm()
        else:
            super().action_batch_import(file_name, file_content)