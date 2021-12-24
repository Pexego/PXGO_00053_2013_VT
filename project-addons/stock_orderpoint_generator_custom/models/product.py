from odoo import models, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        if 'type' in vals and vals['type']=='product':
            orderpoints = self.env['stock.warehouse.orderpoint.template'].search([('all_products','=',True),('auto_generate','=',True)])
            orderpoints.write({'auto_product_ids':[(4,res.id)]})
        return res

