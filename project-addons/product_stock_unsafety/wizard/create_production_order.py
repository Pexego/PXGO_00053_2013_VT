# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, _, exceptions


class CreateProductionOrderWzd(models.TransientModel):

    _name = "create.production.order.wzd"

    def create_production_order(self):
        production_ids = []
        for line in self.env["product.stock.unsafety"].browse(
                self.env.context['active_ids']):
            if not line.bom_id:
                bom = self.env["mrp.bom"]._bom_find(
                    product=line.product_id)
                if not bom:
                    raise exceptions.\
                        Warning(_("Not bom found for product %s") %
                                line.product_id.default_code)
            else:
                bom = line.bom_id.id
            mrp_vals = {'product_id': line.product_id.id,
                        'product_qty': line.product_qty,
                        'bom_id': bom.id,
                        'product_uom_id': line.product_id.uom_id.id,
                        'production_name': line.product_id.default_code}
            mo = self.env["mrp.production"].create(mrp_vals)
            production_ids.append(mo.id)

            line.production_id = mo.id
            line.state = "in_action"

        action = self.env.ref('mrp.mrp_production_action')
        data = action.read()[0]
        data['domain'] = [('id', 'in', production_ids)]
        data['target'] = "parent"
        return data
