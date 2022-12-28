# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
from odoo import http
from odoo.http import request

from odoo.addons.reserve_without_save_sale.controllers.main import WebsiteReservation


class WebsiteReservationIt(WebsiteReservation):

    @http.route(['/reservations/create'],
                type='http', methods=['POST'], auth='user')
    def create_reservation(self, **post):
        """
        This inheritance helps us not to create reservations if the line is dropshipping
        :param post: shows the info of the sale order line
        :return True if the route is dropshipping , otherwise returns the super response
        """
        route = post.get('route_id', False)
        if route:
            route_order = request.env.ref('stock_dropshipping.route_drop_shipping')
            if route_order.id == int(route):
                return json.dumps(True)

        return super(WebsiteReservationIt, self).create_reservation(**post)

    @http.route(['/reservations/write'],
                type='http', methods=['POST'], auth='user')
    def write_reservation(self, **post):
        """
        This inheritance helps us to eliminate reservations in case the line is edited with a dropshipping route
        :param post: shows the info of the sale order line
        :return True if the route is dropshipping , otherwise returns the super response
        """
        route = post.get('route_id', False)
        line = request.env['sale.order.line'].browse(
            int(post['sale_line_id']))
        if route:
            route_order = request.env.ref('stock_dropshipping.route_drop_shipping')
            if route_order.id == int(route):
                line.release_stock_reservation()
                line.write({'unique_js_id': False, 'temp_unique_js_id': False})
                return json.dumps(True)
        return super(WebsiteReservationIt, self).write_reservation(**post)
