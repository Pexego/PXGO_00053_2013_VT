
from odoo import models, fields, api, _, exceptions


class ItalyStockValuation(models.TransientModel):

    _name = 'stock.quantity.history.italy'

    product_id = fields.Many2one('product.product', 'Product')
    qty = fields.Float()
    value = fields.Float()

    @api.multi
    def _get_stock_valuation_italy(self):
        location = self.env['stock.location'].search([('name', '=', 'Depósito Visiotech Italia')])
        products = self.env['product.product'].search([])
        for product in products:
            self.product_id = product
            self.qty = product.with_context({'location': location.id}).qty_available
            self.value = self.qty * product.standard_price_2


class StockQuantityHistory(models.TransientModel):
    _name = 'stock.quantity.history.italy.wizard'
    _description = 'Stock Quantity History Italy'

    compute_at_date = fields.Selection([
        (0, 'Current Inventory'),
       # (1, 'At a Specific Date')
    ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")
    date = fields.Datetime('Inventory at Date', help="Choose a date to get the inventory at that date",
                           default=fields.Datetime.now)

    def open_table(self):
        self.ensure_one()
        tree_view_id = self.env.ref('automatize_edi_es.view_product_italy_stock').id
        ids = []
        location = self.env['stock.location'].search([('name', '=', 'Depósito Visiotech Italia')])

        for product in self.env['product.product'].search([('type', '!=', 'service')]):
            qty = product.with_context({'location': location.id}).qty_available
            value = qty * product.standard_price_2
            prod = self.env['stock.quantity.history.italy'].create({'product_id': product.id,
                                                                    'qty': qty,
                                                                    'value': value})
            ids.append(prod.id)

        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')],
            'view_mode': 'tree',
            'name': _('Products'),
            'res_model': 'stock.quantity.history.italy',
            'context': self.env.context,
            'domain': "[('id','in', " + str(ids) + ")]"
        }
        return action
