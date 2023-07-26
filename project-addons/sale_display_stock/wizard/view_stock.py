from odoo import models, fields, api, _


class ViewStockWizard(models.TransientModel):
    _name = 'view.stock.wizard'

    @api.multi
    def get_stock_lines_field(self, product_id):
        """
        Retrieve the wizard lines related to the specified field in context
        :param product_id:
        :return: A list of wizard lines
        """
        try:
            return getattr(self, f"show_stock_field_{self.env.context.get('stock_field')}")(product_id)
        except AttributeError:
            pass


    def show_stock_field_qty_in_production(self, product_id):
        """
        Retrieve the wizard lines related to the specified product in qty_in_production field.

        :param product_id: The ID of the product for which stock is calculated.
        :return: A list of wizard lines
        """
        moves = self.env["stock.move"].search([('product_id', '=', product_id),
                                               ('purchase_line_id', '!=', False),
                                               ('picking_id', '=', False),
                                               ('state', '!=', 'cancel')])
        wiz_lines = []
        for move in moves:
            wiz_lines.append((0, 0, {'name': move.purchase_line_id.order_id.name, 'qty': move.product_uom_qty,
                                     'purchase_id': move.purchase_line_id.order_id.id}))

        return wiz_lines

    @api.model
    def create(self, vals):
        """
        This method create a wizard with the lines
        :return: wizard created
        """
        lines = self.get_stock_lines_field(vals['product_id'])
        vals['line_ids'] = lines
        return super().create(vals)

    product_id = fields.Many2one('product.product')

    qty = fields.Float()

    line_ids = fields.One2many('view.stock.lines', "wizard_id")

    @api.multi
    def action_show(self):
        """
        This method displays the wizard
        :return: action
        """
        self.ensure_one()
        field_name =  self.env.context.get('stock_field')
        field_display_name = self.product_id._fields[field_name].get_description(self.env)['string']
        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock - %s') % field_display_name,
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }


class ViewStockLines(models.TransientModel):
    _name = 'view.stock.lines'


    wizard_id = fields.Many2one('retry.amazon.orders.wizard')

    name = fields.Char()
    qty = fields.Float()
    purchase_id = fields.Many2one("purchase.order")

    def _show_purchase(self):
        """
        This method displays the view of purchase associated with the line
        :return: action
        """
        action = self.env.ref('purchase.purchase_form_action')
        result = action.read()[0]
        result['context'] = {}
        res = self.env.ref('purchase.purchase_order_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = self.purchase_id.id
        return result

    def open_element(self):
        """
        This method displays the view of the element associated with the line
        :return: action
        """
        if self.purchase_id:
            return self._show_purchase()

