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

from openerp import models, api, exceptions, _, fields
import odoo.addons.decimal_precision as dp
from openerp.tools import float_round


class StockLandedCost(models.Model):

    _inherit = 'stock.landed.cost'

    account_journal_id = fields.Many2one('account.journal', 'Account Journal', required=True,
                                          states={'done': [('readonly', True)]},
                                         default=lambda self: self.env['account.journal'].search([('code', '=', 'APUR')]))

    container_ids = fields.Many2many('stock.container',string='Containers', states={'done': [('readonly', True)]},
                                     copy=False, compute='_get_container')

    @api.one
    def _get_container(self):
        move_obj = self.env['stock.move']
        container_obj = self.env['stock.container']
        res = []
        for picking_id in self.picking_ids:
            move_id = move_obj.search([('picking_id', '=', picking_id.id), ('container_id', '!=', False)], limit=1)
            container_id = container_obj.browse(move_id.container_id.id)
            res.append(container_id.id)

        self.container_ids = res

    def compute_landed_cost(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('stock.valuation.adjustment.lines')
        unlink_ids = line_obj.search(cr, uid, [('cost_id', 'in', ids)],
                                     context=context)
        line_obj.unlink(cr, uid, unlink_ids, context=context)
        digits = dp.get_precision('Product Price')(cr)
        towrite_dict = {}
        for cost in self.browse(cr, uid, ids, context=None):
            if not cost.picking_ids:
                continue
            picking_ids = [p.id for p in cost.picking_ids]
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            total_tariff = 0.0
            vals = self.get_valuation_lines(cr, uid, [cost.id],
                                            picking_ids=picking_ids,
                                            context=context)
            for v in vals:
                for line in cost.cost_lines:
                    v.update({'cost_id': cost.id, 'cost_line_id': line.id})
                    self.pool.get('stock.valuation.adjustment.lines').\
                        create(cr, uid, v, context=context)
                total_qty += v.get('quantity', 0.0)
                total_cost += v.get('former_cost', 0.0)
                total_weight += v.get('weight', 0.0)
                total_volume += v.get('volume', 0.0)
                total_tariff += v.get('tariff', 0.0)
                total_line += 1

            for line in cost.cost_lines:
                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and \
                            valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and \
                                total_cost:
                            per_unit = (line.price_unit / total_cost)
                            value = valuation.former_cost * per_unit
                        elif line.split_method == 'by_tariff' and total_tariff:
                            per_unit = (line.price_unit / total_tariff)
                            value = valuation.tariff * per_unit
                        else:
                            value = (line.price_unit / total_line)

                        if digits:
                            value = float_round(value,
                                                precision_digits=digits[1],
                                                rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
        if towrite_dict:
            for key, value in towrite_dict.items():
                line_obj.write(cr, uid, key, {'additional_landed_cost': value},
                               context=context)
        return True

    def get_valuation_lines(self, cr, uid, ids, picking_ids=None,
                            context=None):
        picking_obj = self.pool.get('stock.picking')
        lines = []
        if not picking_ids:
            return lines

        for picking in picking_obj.browse(cr, uid, picking_ids):
            for move in picking.move_lines:
                #it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
                if move.product_id.cost_method != 'real':
                    continue
                total_cost = 0.0
                total_qty = move.product_qty
                weight = move.weight or (move.product_id and \
                    move.product_id.weight * move.product_qty)
                volume = move.product_id and move.product_id.volume * \
                    move.product_qty
                for quant in move.quant_ids:
                    total_cost += (quant.cost * quant.qty)
                tariff = move.product_id and move.product_id.tariff * \
                    move.product_qty
                vals = dict(product_id=move.product_id.id, move_id=move.id,
                            quantity=move.product_uom_qty,
                            former_cost=total_cost, weight=weight,
                            volume=volume, tariff=tariff)
                lines.append(vals)
        return lines

    def button_validate(self, cr, uid, ids, context=None):
        res = super(StockLandedCost, self).button_validate(cr, uid, ids, context)
        for cost in self.browse(cr, uid, ids, context=context):
            for line in cost.valuation_adjustment_lines:
                if line.product_id.cost_method == 'real':
                    self.pool.get('product.product').update_real_cost(cr, uid, line.product_id.id, context)
        return res
        '''quant_obj = self.pool.get('stock.quant')
        product_obj = self.pool.get('product.product')

        for cost in self.browse(cr, uid, ids, context=context):
            if not cost.valuation_adjustment_lines or not self._check_sum(cr, uid, cost, context=context):
                raise exceptions.except_orm(_('Error!'), _('You cannot validate a landed cost which has no valid valuation lines.'))
            move_id = self._create_account_move(cr, uid, cost, context=context)
            quant_dict = {}
            for line in cost.valuation_adjustment_lines:
                if not line.move_id:
                    continue
                if line.product_id.cost_method == 'average':
                    # (((ctdad_total - ctdad_move) * precio_coste_antes_mov) + (ctdad_move * precio_coste + costes)) / ctdad_total
                    # average_price = (((line.product_id.qty_available - line.move_id.product_qty) * line.product_id.standard_price) + (line.move_id.product_qty * (line.product_id.standard_price + line.additional_landed_cost))) / line.product_id.qty_available
                    average_price = line.product_id.standard_price + \
                        (line.additional_landed_cost /
                         line.move_id.product_qty)
                    product_obj.write(cr, uid, [line.product_id.id],
                                      {'standard_price': average_price},
                                      context)
                per_unit = line.final_cost / line.quantity
                diff = per_unit - line.former_cost_per_unit
                quants = [quant for quant in line.move_id.quant_ids]
                for quant in quants:
                    if quant.id not in quant_dict:
                        quant_dict[quant.id] = quant.cost + diff
                    else:
                        quant_dict[quant.id] += diff
                for key, value in quant_dict.items():
                    quant_obj.write(cr, 1, key, {'cost': value},
                                    context=context)
                qty_out = 0
                for quant in line.move_id.quant_ids:
                    if quant.location_id.usage != 'internal':
                        qty_out += quant.qty
                self._create_accounting_entries(cr, uid, line, move_id,
                                                qty_out, context=context)
            self.write(cr, uid, cost.id, {'state': 'done',
                                          'account_move_id': move_id},
                       context=context)
        return True'''


class StockValuationAdjustmentLines(models.Model):

    _inherit = 'stock.valuation.adjustment.lines'

    standard_price = fields.Float('Standard price')
    new_standard_price = fields.Float('New standard price')
    tariff = fields.Float("Tariff", digits=(16, 2))

    @api.multi
    def write(self, vals):
        if vals.get('additional_landed_cost', False):
            vals['standard_price'] = \
                sum(self.move_id.mapped('quant_ids.inventory_value')) / \
                sum(self.move_id.mapped('quant_ids.qty'))
            vals['new_standard_price'] = (
                sum(self.move_id.mapped('quant_ids.inventory_value')) +
                vals['additional_landed_cost']) / sum(self.move_id.mapped('quant_ids.qty'))
        return super(StockValuationAdjustmentLines, self).write(vals)


class StockLandedCostLines(models.Model):
    _inherit = 'stock.landed.cost.lines'

    split_method = fields.Selection(selection_add=[('by_tariff',
                                                    'By tariff')])

    def onchange_product_id(self, cr, uid, ids, product_id=False,
                            context=None):
        result = super(StockLandedCostLines, self).\
            onchange_product_id(cr, uid, ids, product_id, context)

        if product_id and result.get('value', False):
            product = self.pool.get('product.product').\
                browse(cr, uid, product_id, context=context)
            stock_input_acc = product.property_stock_account_input and \
                product.property_stock_account_input.id or False
            if not stock_input_acc:
                stock_input_acc = \
                    product.categ_id.property_stock_account_input_categ and \
                    product.categ_id.property_stock_account_input_categ.id or \
                    False
            result['value']['account_id'] = stock_input_acc

        return result
