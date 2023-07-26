from odoo import models, fields, api, _


class ViewStockWizard(models.TransientModel):
    _inherit = 'view.stock.wizard'


    def show_stock_field_qty_in_production(self, product_id):
        """
        Retrieve the wizard lines related to the specified product in qty_in_production field.

        :param product_id: The ID of the product for which stock is calculated.
        :return: A list of wizard lines
        """
        res = super().show_stock_field_qty_in_production(product_id)
        order_lines = self.env["purchase.order.line"].search([('product_id', '=', product_id),
                                                    ('order_id.state', '=', 'purchase_order'),
                                                    ('order_id.completed_purchase','=',False)])

        for line in order_lines.filtered(lambda l:l.production_qty > 0):
            res.append((0, 0, {'name': line.order_id.name, 'qty': line.production_qty,
                              'purchase_id': line.order_id.id}))

        return res


