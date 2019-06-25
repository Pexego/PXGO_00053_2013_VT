# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WebsiteReservation(http.Controller):

    @http.route(['/reservations/create'],
                type='http', methods=['POST'], auth='user')
    def create_reservation(self, **post):
        warehouse = request.env['stock.warehouse'].browse(
            int(post['warehouse']))
        product = request.env['product.product'].browse(
            int(post['product_id']))
        if product.type == "product":
            vals = {
                'product_id': int(post['product_id']),
                'product_uom': int(post['uom']),
                'product_uom_qty': float(post['qty']),
                'date_validity': False,
                'name': post.get('name', product.default_code),
                'location_id': warehouse.lot_stock_id.id,
                'price_unit': float(post['price_unit']),
                'unique_js_id': post['unique_js_id']
            }
            if post.get('order_id'):
                sale = request.env['sale.order'].browse(int(post['order_id']))
                if not sale.procurement_group_id:
                    group_id = self.env['procurement.group'].create({
                            'name': sale.name,
                            'move_type': sale.picking_policy,
                            'sale_id': sale.id,
                            'partner_id': sale.partner_shipping_id.id})
                    sale.procurement_group_id = group_id.id
                vals['group_id'] = sale.procurement_group_id.id
            new_reservation = request.env['stock.reservation'].create(vals)
            new_reservation.reserve()
            line_ids = request.env['sale.order.line'].search(
                [('unique_js_id', '=', post['unique_js_id'])])
            if line_ids:
                new_reservation.write({'sale_line_id': line_ids[0]})
        return json.dumps(True)

    @http.route(['/reservations/unlink'],
                type='http', methods=['POST'], auth='user')
    def unlink_reservation(self, **post):
        unique_js_id = int(post['unique_js_id'])
        reservation = request.env['stock.reservation'].search(
            [('unique_js_id', '=', unique_js_id)])
        reservation.unlink()
        return json.dumps(True)

    @http.route(['/reservations/write'],
                type='http', methods=['POST'], auth='user')
    def write_reservation(self, **post):
        """
            Si se ha modificado el producto, se elimina la reserva y se crea
            una nueva.
            Si solo se modifica la cantidad se escribe.
        """
        if post.get('product_id', False):
            product = request.env['product.product'].browse(
                int(post['product_id']))
            if product.type == "product":
                reservation = request.env['stock.reservation'].search(
                    [('unique_js_id', '=', post['unique_js_id'])])
                if reservation.product_id.id != product.id:
                    # Creamos una nueva reserva.
                    warehouse = request.env['stock.warehouse'].browse(
                        int(post['warehouse']))
                    vals = {
                        'product_id': int(post['product_id']),
                        'product_uom': int(post['uom']),
                        'product_uom_qty': float(post['qty']),
                        'date_validity': False,
                        'name': post.get('name', product.default_code),
                        'location_id': warehouse.lot_stock_id.id,
                        'price_unit': float(post['price_unit']),
                        'unique_js_id': post['new_js_unique_id'],
                    }
                    reserve = reservation.copy(vals)
                    reserve.reserve()
                    reservation.unlink()
                    return json.dumps(
                        {'unique_js_id': post['new_js_unique_id']})
                else:
                    # Solo nos importan los cambios en cantidad
                    reservation.write({'product_uom_qty': float(post['qty'])})
        return json.dumps(True)
