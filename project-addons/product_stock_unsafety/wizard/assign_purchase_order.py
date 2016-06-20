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


class AssignPurchaseOrderWzd(models.TransientModel):

    _name = "assign.purchase.order.wzd"

    purchase_id = fields.Many2one("purchase.order", "Purchase",
                                  domain=[('state', '=', 'draft')])


    @api.multi
    def assign_purchase_order(self):
        obj = self[0]
        unsafety_obj = self.env["product.stock.unsafety"]
        view_obj = self.env["ir.ui.view"]
        purchase_line_obj = self.env["purchase.order.line"]
        for line in unsafety_obj.browse(self.env.context['active_ids']):
            line.purchase_id = obj.purchase_id
            line.state = "in_action"
            line.supplier_id = obj.purchase_id.partner_id.id
            purchase = obj.purchase_id
            line_vals = {'order_id': purchase.id,
                         'product_id': line.product_id.id,
                         'price_unit': 0.0}
            line_vals.update(purchase_line_obj.
                             onchange_product_id(purchase.pricelist_id.id,
                                                 line.product_id.id,
                                                 line.product_qty,
                                                 line.product_id.uom_id.id,
                                                 purchase.partner_id.id,
                                                 purchase.date_order,
                                                 purchase.fiscal_position.id,
                                                 purchase.minimum_planned_date)
                             ['value'])
            if line_vals.get('taxes_id', False):
                line_vals['taxes_id'] = [(6, 0, line_vals['taxes_id'])]
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
