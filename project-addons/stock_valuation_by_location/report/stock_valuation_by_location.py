from odoo import models, fields, api,_

class StockValuationByLoc(models.TransientModel):
    _name = 'stock.valuation.by.location'

    product_id = fields.Many2one('product.product',"Product")
    qty = fields.Float("Quantity")
    location_id = fields.Many2one('stock.location','Location')
    value = fields.Float("Value")

class StockQuantityHistory(models.TransientModel):
    _name = 'stock.valuation.by.location.wizard'
    compute_at_date = fields.Selection([
        (0, 'Current Inventory'),
        (1, 'At a Specific Date')
        ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")
    date = fields.Datetime('Inventory at Date', help="Choose a date to get the inventory at that date",
        default=fields.Datetime.now)

    def open_table(self):
        self.ensure_one()
        tree_view_id = self.env.ref('stock_valuation_by_location.view_stock_inventory_by_location').id
        ids = []
        for product in self.env['product.product'].search([('type', '=', 'product')]):
            for location in self.env['stock.location'].search([('usage','=','internal')]):
                qty = product.with_context(dict({'location': location.id},to_date=self.date)).qty_available
                if qty!=0:
                    value = qty * product.standard_price_2
                    prod = self.env['stock.valuation.by.location'].create({'product_id': product.id,
                                                                        'qty': qty,
                                                                        'value': value,
                                                                        'location_id':location.id})
                    ids.append(prod.id)
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')],
            'view_mode': 'tree',
            'name': _('Products'),
            'res_model': 'stock.valuation.by.location',
            'context': self.env.context,
            'domain': "[('id','in', " + str(ids) + ")]"
             }
        return action