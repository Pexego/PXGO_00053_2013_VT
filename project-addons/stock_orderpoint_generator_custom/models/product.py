from odoo import models, api, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        if 'type' in vals and vals['type']=='product':
            orderpoints = self.env['stock.warehouse.orderpoint.template'].search([('all_products','=',True),('auto_generate','=',True)])
            orderpoints.write({'auto_product_ids':[(4,res.id)]})
        return res

    @api.multi
    def _get_waiting_reservation_count(self):
        for product in self:
            reservations_confirmed = self.env['stock.reservation'].search(
                [('product_id', '=', product.id), ('state', '=', 'confirmed')])
            reservations_partially = self.env['stock.reservation'].search(
                [('product_id', '=', product.id), ('state', '=', 'partially_available')])
            product.waiting_reservation_count = sum(reservations_confirmed.mapped('product_qty')) + \
                                                sum(reservations_partially.mapped('product_qty')) - \
                                                sum(reservations_partially.mapped('reserved_availability'))

    waiting_reservation_count = fields.Float(compute="_get_waiting_reservation_count",
                                             help="This field shows the unavailable quantity of this product in reservations")

    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        res = super(ProductProduct, self)._compute_quantities_dict(lot_id, owner_id, package_id, from_date, to_date)
        if res and self._context.get('modify_stock_qty', False):
            for product_id in res.keys():
                product = self.env['product.product'].browse(product_id)
                product_stock= res[product_id]
                w_res_count = product.waiting_reservation_count
                res[product_id]['outgoing_qty'] -= w_res_count
                moves_to_location = self.env['stock.move'].search(
                    [('product_id', '=', product_id), ('state', 'not in', ['draft','done', 'cancel']),
                     ('location_dest_id', '=', self._context.get('location')),
                     ('location_id', '=', self.env.ref('automatize_edi_it.stock_location_vendor_deposit').id)])
                res[product_id]['incoming_qty'] = sum(moves_to_location.mapped('product_qty'))
                res[product_id]['virtual_available'] = product_stock['qty_available'] + product_stock['incoming_qty']\
                                                       - product_stock['outgoing_qty']
        return res
