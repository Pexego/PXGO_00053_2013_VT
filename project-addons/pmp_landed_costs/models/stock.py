from odoo import models, fields


class StockContainer(models.Model):

    _inherit = 'stock.container'

    import_sheet_ids = fields.One2many(
        "import.sheet",
        "container_id",
        string="Import Sheets",
        required=True
    )
    import_sheet_count = fields.Integer(compute='_get_import_sheet_count', default=0)

    def _get_import_sheet_count(self):
        """
        Gets the list of import_sheet associated with the container and calculates
        the count of them.
        """
        for container in self:
            container.import_sheet_count = len(container.import_sheet_ids)

    def action_view_sheets(self):

        action = self.env.ref('pmp_landed_costs.action_stock_container_import_sheets').read()[0]

        action['domain'] = [('id', 'in', self.import_sheet_ids.ids)]

        return action
