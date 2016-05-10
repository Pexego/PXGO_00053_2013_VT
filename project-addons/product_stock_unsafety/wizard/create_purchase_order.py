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


class CreatePurchaseFromUnsafetyWzd(models.TransientModel):

    _name = "create.purchase.from.unsafety.wzd"

    @api.model
    def default_get(self, fields_list):
        defaults = super(CreatePurchaseFromUnsafetyWzd, self).\
            default_get(fields_list)
        if self.env.context.get('active_ids', False):
            unsafety_obj = self.env["product.stock.unsafety"]
            for unsafety in unsafety_obj.\
                    browse(self.env.context['active_ids']):
                if unsafety.supplier_id:
                    defaults['supplier_id'] = unsafety.supplier_id.id
                    defaults['warehouse_id'] = unsafety.orderpoint_id.\
                        warehouse_id.id
                    break
        return defaults

    supplier_id = fields.Many2one("res.partner", "Supplier", required=True,
                                  domain=[('supplier', '=', True),
                                          ('is_company', '=', True)])
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse",
                                   required=True)

    @api.multi
    def create_purchase_order(self):
        obj = self[0]
        purchase_obj = self.env["purchase.order"]
        purchase_line_obj = self.env["purchase.order.line"]
        unsafety_obj = self.env["product.stock.unsafety"]
        view_obj = self.env["ir.ui.view"]
        purchase_vals = {'partner_id': obj.supplier_id.id,
                         'picking_type_id': obj.warehouse_id.in_type_id.id,
                         'location_id': obj.warehouse_id.
                         wh_input_stock_loc_id.id}
        purchase_vals.update(purchase_obj.
                             onchange_partner_id(obj.supplier_id.id)['value'])
        purchase = purchase_obj.create(purchase_vals)
        for line in unsafety_obj.browse(self.env.context['active_ids']):
            line_vals = {'order_id': purchase.id,
                         'product_id': line.product_id.id}
            line_vals.update(purchase_line_obj.
                             onchange_product_id(purchase.pricelist_id.id,
                                                 line.product_id.id,
                                                 line.product_qty,
                                                 line.product_id.uom_id.id,
                                                 purchase.partner_id.id)
                             ['value'])
            purchase_line_obj.create(line_vals)
            line.purchase_id = purchase.id
            line.state = "in_action"
            line.supplier_id = obj.supplier_id.id

        view = view_obj.search([('model', '=', "purchase.order"),
                                ('type', '=', 'form')])[0]
        return {'name': _("Purchase Order"),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view.id,
                'res_model': "purchase.order",
                'res_id': purchase.id,
                'type': 'ir.actions.act_window'}
