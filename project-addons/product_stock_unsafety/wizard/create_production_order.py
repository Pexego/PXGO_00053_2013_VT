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

from openerp import models, api, _, exceptions


class CreateProductionOrderWzd(models.TransientModel):

    _name = "create.production.order.wzd"

    @api.multi
    def create_production_order(self):
        mrp_obj = self.env["mrp.production"]
        bom_obj = self.env["mrp.bom"]
        unsafety_obj = self.env["product.stock.unsafety"]
        production_ids = []
        for line in unsafety_obj.browse(self.env.context['active_ids']):
            if not line.bom_id:
                bom_id = bom_obj._bom_find(product_id=line.product_id.id)
                if not bom_id:
                    raise exceptions.\
                        Warning(_("Not bom found for product %s") %
                                line.product_id.default_code)
            else:
                bom_id = line.bom_id.id
            mrp_vals = {'product_id': line.product_id.id,
                        'product_qty': line.product_qty,
                        'bom_id': bom_id,
                        'product_uom': line.product_id.uom_id.id,
                        'production_name': line.product_id.default_code}
            mo = mrp_obj.create(mrp_vals)
            mo.signal_workflow('button_confirm')
            production_ids.append(mo.id)

            line.production_id = mo.id
            line.state = "in_action"

        action = self.env.ref('mrp.mrp_production_action')
        data = action.read()[0]
        data['domain'] = [('id', 'in', production_ids)]
        data['target'] = "parent"
        return data
