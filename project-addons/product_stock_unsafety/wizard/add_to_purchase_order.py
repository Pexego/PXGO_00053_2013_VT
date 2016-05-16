# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from openerp import models, fields, api, _


class AddToPurchaseOrderWzd(models.TransientModel):

    _name = "add.to.purchase.order.wzd"

    purchase_id = fields.Many2one("purchase.order", "Purchase",
                                  required=True, domain=[('state', '=',
                                                          'draft')])
    purchase_qty = fields.Float("Qty. to purchase", required=True)

    @api.multi
    def assign_purchase_order(self):
        obj = self[0]
        product_obj = self.env["product.product"]
        view_obj = self.env["ir.ui.view"]
        purchase_line_obj = self.env["purchase.order.line"]
        for product in product_obj.browse(self.env.context['active_ids']):
            purchase = obj.purchase_id
            line_vals = {'order_id': purchase.id,
                         'product_id': product.id}
            line_vals.update(purchase_line_obj.
                             onchange_product_id(purchase.pricelist_id.id,
                                                 product.id, obj.purchase_qty,
                                                 product.uom_id.id,
                                                 purchase.partner_id.id)
                             ['value'])
            purchase_line_obj.create(line_vals)

        view = view_obj.search([('model', '=', "purchase.order"),
                                ('type', '=', 'form')])[0]
        return {'name': _("Purchase Order"),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view.id,
                'res_model': "purchase.order",
                'res_id': obj.purchase_id.id,
                'type': 'ir.actions.act_window'}
