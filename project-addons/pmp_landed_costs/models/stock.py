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

    def get_products_for_landed_cost_warning(self):
        """
        Returns container products that have no weight or no hs_code_id or no volume

        Returns:
        -------
        product.product
        """
        return self.move_ids.mapped('product_id').filtered(
            lambda product: product.weight == 0 or not product.hs_code_id or product.volume == 0
        )
