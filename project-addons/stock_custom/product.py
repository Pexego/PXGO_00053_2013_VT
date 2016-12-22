# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, _, fields

class ProductProduct(models.Model):

    _inherit = 'product.product'

    virtual_stock_cooked = fields.Float('Stock Available Cooking', compute="_get_virtual_stock_cooked")

    @api.multi
    def _get_virtual_stock_cooked(self):
        for product in self:
            product.virtual_stock_cooked = product.qty_available_wo_wh +\
                                            product.virtual_stock_conservative

    @api.multi
    def action_view_moves(self):
        return {
            'domain': "[('product_id','=', " + str(self.id) + ")]",
            'name': _('Stock moves'),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': {'tree_view_ref': 'stock.view_move_tree',
                        'search_default_groupby_dest_location_id': 1,
                        'search_default_ready': 1,
                        'search_default_future': 1},
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
        }


    @api.multi
    def update_real_cost(self):
        for product in self:
            quants = self.env['stock.quant'].search([('location_id.usage', '=', 'internal'), ('product_id', '=', product.id)])
            if sum(quants.mapped('qty')) != 0:
                standard_price = sum(quants.mapped('inventory_value')) / sum(quants.mapped('qty'))
                dp = self.env['decimal.precision'].search([('name', '=', 'Product Price')])
                standard_price = round(standard_price, dp.digits)
                if standard_price != round(product.standard_price, dp.digits):
                    product.standard_price = standard_price


    @api.model
    def cron_update_product_real_cost(self):
        products = self.env['product.product'].search([('cost_method', '=', 'real')])
        products.update_real_cost()
