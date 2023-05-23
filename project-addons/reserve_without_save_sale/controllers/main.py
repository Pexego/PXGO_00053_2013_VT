# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import logging
from odoo import http
from odoo.http import request
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class WebsiteReservation(http.Controller):

    @staticmethod
    def _get_date_validity(infinite_reservation):
        """ Calculate the date validity of the reservation
        :param infinite_reservation: it can be 'true' or 'false'
        :return: Validity date based on inifine_reservation parameter
        """
        now = datetime.now()
        if json.loads(infinite_reservation):
            date_validity = (now + relativedelta(days=365)).strftime("%Y-%m-%d")
        else:
            days_release_reserve = request.env['ir.config_parameter'].sudo().get_param('days_to_release_reserve_stock')
            date_validity = (now + relativedelta(days=int(days_release_reserve))).strftime("%Y-%m-%d")
        return date_validity

    @http.route(['/reservations/create'],
                type='http', methods=['POST'], auth='user')
    def create_reservation(self, **post):
        date_validity = self._get_date_validity(post.get('infinite_reservation','false'))
        warehouse = request.env['stock.warehouse'].browse(
            int(post['warehouse']))
        product = request.env['product.product'].browse(
            int(post['product_id']))
        if product.type == "product":
            vals = {
                'product_id': int(post['product_id']),
                'product_uom': int(post['uom']),
                'product_uom_qty': float(post['qty']),
                'date_validity': date_validity,
                'name': post.get('name', product.default_code),
                'location_id': warehouse.lot_stock_id.id,
                'sale_line_id': post['sale_line_id'] != 'false' and int(post['sale_line_id']) or False,
                'sale_id': post['sale_id'] != 'false' and int(post['sale_id']) or False,
                'user_id': post['user_id'] != 'false' and int(post['user_id']) or False,
                'price_unit': float(post['price_unit']),
                'unique_js_id': post['unique_js_id']
            }
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
        date_validity = self._get_date_validity(post.get('infinite_reservation','false'))
        if post.get('product_id', False):
            product = request.env['product.product'].browse(
                int(post['product_id']))
            warehouse = request.env['stock.warehouse'].browse(
                int(post['warehouse']))
            if product.type == "product":
                reservation = request.env['stock.reservation'].search(
                    [('unique_js_id', '=', post['unique_js_id'])]) or \
                              post['sale_line_id'] != 'false' and \
                              request.env['stock.reservation'].search(
                                  [('sale_line_id', '=', int(post['sale_line_id']))])
                if reservation:
                    if len(reservation) > 1 or reservation.product_id.id != product.id:
                        # Si es un kit (puede tener 1 o varias líneas de reserva, pero el id de producto no coincide)
                        # O si se cambia el producto de la línea del pedido por otro
                        # Creamos una nueva reserva.
                        vals = {
                            'product_id': int(post['product_id']),
                            'product_uom': int(post['uom']),
                            'product_uom_qty': float(post['qty']),
                            'date_validity': date_validity,
                            'sale_line_id': post['sale_line_id'] != 'false' and int(post['sale_line_id']) or False,
                            'sale_id': post['sale_id'] != 'false' and int(post['sale_id']) or False,
                            'user_id': post['user_id'] != 'false' and int(post['user_id']) or False,
                            'name': post.get('name', product.default_code),
                            'location_id': warehouse.lot_stock_id.id,
                            'price_unit': float(post['price_unit']),
                            'unique_js_id': post['new_js_unique_id'],
                        }
                        new_reservation = request.env['stock.reservation'].create(vals)
                        new_reservation.reserve()
                        reservation.unlink()
                        return json.dumps({'unique_js_id': post['new_js_unique_id']})
                    else:
                        if reservation.product_uom_qty != float(post['qty']):
                            # Solo nos importan los cambios en cantidad
                            reservation.write({'product_uom_qty': float(post['qty'])})
                            reservation.reserve()
                            reservation.move_id._recompute_state()
        return json.dumps(True)
