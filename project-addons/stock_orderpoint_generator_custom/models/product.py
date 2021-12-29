from odoo import models, api, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        orderpoints = self.env['stock.warehouse.orderpoint.template'].search([('all_products','=',True),('auto_generate','=',True)])
        orderpoints.write({'auto_product_ids':[(4,res.id)]})
        return res

    @api.multi
    def _get_waiting_reservation_count(self):
        for product in self:
            reservations_confirmed = self.env['stock.reservation'].search([('product_id', '=', product.id),('state', '=', 'confirmed')])
            reservations_partially = self.env['stock.reservation'].search([('product_id', '=', product.id), ('state', '=', 'partially_available')])
            product.waiting_reservation_count = sum(reservations_confirmed.mapped('product_qty')) + \
                                                sum(reservations_partially.mapped('product_qty')) - \
                                                sum(reservations_partially.mapped('reserved_availability'))

    waiting_reservation_count = fields.Float(compute="_get_waiting_reservation_count",
                                             help="This field shows the unavailable quantity of this product in reservations")

