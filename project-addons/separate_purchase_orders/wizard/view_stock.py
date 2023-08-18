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

class ViewStockLines(models.TransientModel):
    _inherit = 'view.stock.lines'


    def _show_separate_purchase_order(self):
        """
        This method displays the view of OC associated with the line
        :return: action
        """
        action = self.env.ref('separate_purchase_orders.action_open_purchase_orders_in_purchase_order_state')
        result = action.read()[0]
        res = self.env.ref('separate_purchase_orders.purchase_order_form_custom', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = self.purchase_id.id
        return result

    def open_element(self):
        """
        This method displays the view of the element associated with the line
        :return: action
        """

        if self.purchase_id and self.purchase_id.state=='purchase_order':
            return self._show_separate_purchase_order()
        return super().open_element()


