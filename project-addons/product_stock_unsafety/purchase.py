# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos S.L.
#    $Omar Castiñeira Saavedra$ <omar@comunitea.com>
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
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def wkf_confirm_order(self):
        """
        When confirm a purchase order, if purchase order was created from a
        pre order, we try to find under minimum alerts with the same pre orders
        (That means really that purchase was created from a under minimum) in
        'In purchase' state and we finish it
        """
        res = super(PurchaseOrder, self).wkf_confirm_order()
        under_min = self.env['product.stock.unsafety']
        for po in self:
            domain = [
                ('state', '=', 'in_action'),
                ('purchase_id', '=', po.id)
            ]
            under_min_objs = under_min.search(domain)
            if under_min_objs:
                under_min_objs.write({'state': 'finalized'})
        return res

    @api.multi
    def unlink(self):
        under_min_obj = self.env['product.stock.unsafety']
        for order in self:
            under_mins = under_min_obj.search([('purchase_id', '=', order.id)])
            if under_mins:
                under_mins.write({"state": "in_progress",
                                  "purchase_id": False})
        return super(PurchaseOrder, self).unlink()


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    @api.multi
    def unlink(self):
        under_min_obj = self.env['product.stock.unsafety']
        for line in self:
            under_mins = under_min_obj.search([('purchase_id', '=',
                                                line.order_id.id),
                                               ('product_id', '=',
                                                line.product_id.id)])
            if under_mins:
                under_mins.write({"state": "in_progress",
                                  "purchase_id": False})
        return super(PurchaseOrderLine, self).unlink()
