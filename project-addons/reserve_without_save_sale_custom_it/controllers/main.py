# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
from odoo import http
from odoo.http import request

from odoo.addons.reserve_without_save_sale.controllers.main import WebsiteReservation


class WebsiteReservationIt(WebsiteReservation):

    @http.route(['/reservations/create'],
                type='http', methods=['POST'], auth='user')
    def create_reservation(self, **post):
        route = post.get('route_id', False)
        if route:
            route_order = request.env.ref('stock_dropshipping.route_drop_shipping')
            if route_order.id == int(route):
                return json.dumps(True)

        return super(WebsiteReservationIt, self).create_reservation(**post)
