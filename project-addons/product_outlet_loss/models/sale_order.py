##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sanchez <kiko@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from odoo import models, fields, api, exceptions
from datetime import date
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        res = super().action_confirm()

        if self:
            for line in self.order_line:
                if line.product_id.is_outlet:
                    values = {
                        'qty': line.product_uom_qty,
                        'price_outlet': line.price_subtotal/line.product_uom_qty,
                        'price_unit': line.product_id.commercial_cost,
                        'product_id': line.product_id.id,
                        'date_move': line.order_id.date_order,
                        'outlet_ok': False,
                        'order_line_id': line.id
                    }
                    nuevo = self.env['outlet.loss'].create(values)

        return res

    @api.multi
    def action_cancel(self):

        res = super(SaleOrder, self).action_cancel()
        if self:
            for line in self.order_line:
                if line.product_id.is_outlet:
                    self.env['outlet.loss'].search([('order_line_id', '=', line.id)]).unlink()

        return res



