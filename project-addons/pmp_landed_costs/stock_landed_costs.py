# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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

from openerp import models, api, exceptions, _
from openerp.osv import fields

class StockLandedCost(models.Model):

    _inherit = 'stock.landed.cost'

    _columns = {
        'account_journal_id': fields.many2one('account.journal', 'Account Journal', required=False),
    }

    def get_valuation_lines(self, cr, uid, ids, picking_ids=None, context=None):
        picking_obj = self.pool.get('stock.picking')
        lines = []
        if not picking_ids:
            return lines

        for picking in picking_obj.browse(cr, uid, picking_ids):
            for move in picking.move_lines:
                #it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
                total_cost = 0.0
                total_qty = move.product_qty
                weight = move.product_id and move.product_id.weight * move.product_qty
                volume = move.product_id and move.product_id.volume * move.product_qty
                for quant in move.quant_ids:
                    total_cost += quant.cost
                vals = dict(product_id=move.product_id.id, move_id=move.id, quantity=move.product_uom_qty, former_cost=total_cost * total_qty, weight=weight, volume=volume)
                lines.append(vals)
        return lines

    def button_validate(self, cr, uid, ids, context=None):
        quant_obj = self.pool.get('stock.quant')
        product_obj = self.pool.get('product.product')

        for cost in self.browse(cr, uid, ids, context=context):
            if not cost.valuation_adjustment_lines or not self._check_sum(cr, uid, cost, context=context):
                raise exceptions.except_orm(_('Error!'), _('You cannot validate a landed cost which has no valid valuation lines.'))
            quant_dict = {}
            for line in cost.valuation_adjustment_lines:
                if not line.move_id:
                    continue
                if line.product_id.cost_method == 'average':
                    # (((ctdad_total - ctdad_move) * precio_coste_antes_mov) + (ctdad_move * precio_coste + costes)) / ctdad_total
                    # average_price = (((line.product_id.qty_available - line.move_id.product_qty) * line.product_id.standard_price) + (line.move_id.product_qty * (line.product_id.standard_price + line.additional_landed_cost))) / line.product_id.qty_available
                    average_price = (line.product_id.qty_available * line.product_id.standard_price + line.additional_landed_cost) / line.product_id.qty_available
                    product_obj.write(cr, uid, [line.product_id.id], {'standard_price_cost': average_price}, context)
                per_unit = line.final_cost / line.quantity
                diff = per_unit - line.former_cost_per_unit
                quants = [quant for quant in line.move_id.quant_ids]
                for quant in quants:
                    if quant.id not in quant_dict:
                        quant_dict[quant.id] = quant.cost + diff
                    else:
                        quant_dict[quant.id] += diff
                for key, value in quant_dict.items():
                    quant_obj.write(cr, 1, key, {'cost': value}, context=context)
                qty_out = 0
                for quant in line.move_id.quant_ids:
                    if quant.location_id.usage != 'internal':
                        qty_out += quant.qty
            self.write(cr, uid, cost.id, {'state': 'done'}, context=context)
        return True
