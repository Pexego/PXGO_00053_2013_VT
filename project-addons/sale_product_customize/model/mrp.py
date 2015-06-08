# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
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

from openerp import models, api


class MrpProduction(models.Model):

    _inherit = "mrp.production"

    @api.multi
    def action_production_end(self):
        produce_wzd = self.env["mrp.product.produce"]
        pline_wzd = self.env["mrp.product.produce.line"]
        for prod in self:
            for fmove in prod.move_created_ids:
                wzd = produce_wzd.create({"product_id": fmove.product_id.id,
                                          "product_qty": fmove.product_uom_qty,
                                          "mode": "consume_produce",
                                          "lot_id": fmove.restrict_lot_id and
                                          fmove.restrict_lot_id.id or False})
                for line in prod.move_lines:
                    pline_wzd.create({"product_id": line.product_id.id,
                                      "product_qty": line.product_uom_qty,
                                      "lot_id": line.restrict_lot_id and
                                      line.restrict_lot_id.id or False,
                                      "produce_id": wzd.id})
                wzd.with_context(active_id=prod.id).do_produce()
            if prod.test_production_done():
                prod.state = "done"

        return True
