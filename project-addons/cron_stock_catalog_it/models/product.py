from odoo import models, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _get_eol_stock_move_domain(self, date):
        """ :returns the super domain adding not dropship picking """
        domain = super()._get_eol_stock_move_domain(date)
        dropship_route = self.env.ref('stock_dropshipping.picking_type_dropship')
        return domain + [('picking_id.picking_type_id', '!=', dropship_route.id)]
