# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Omar Castiñeira Saavedra
#    Copyright 2015 Comunitea Servicios Tecnológicos S.L.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    @api.depends('move_lines.state', 'move_lines.picking_id',
                 'move_lines.product_id', 'move_lines.product_uom_qty',
                 'move_lines.product_uom')
    def _cal_weight(self):
        for picking in self:
            total_weight = total_weight_net = 0.00
            for move in picking.move_lines:
                if move.state != 'cancel':
                    total_weight += move.weight
                    total_weight_net += move.weight_net
            if picking.weight_st:
                total_weight = picking.weight_st
            if picking.weight_net_st:
                total_weight_net = picking.weight_net_st
            picking.weight = total_weight
            picking.weight_net = total_weight_net

    @api.model
    def _get_default_uom(self):
        uom_categ_id = self.env.ref('product.product_uom_categ_kgm')
        return self.env['product.uom'].search([('category_id', '=',
                                                uom_categ_id.id),
                                               ('factor', '=', 1)])[0]

    @api.multi
    def write(self, vals):
        if 'weight' in vals:
            vals['weight_st'] = vals.get('weight')
        if 'weight_net' in vals:
            vals['weight_net_st'] = vals.get('weight_net')
        return super(StockPicking, self).write(vals)

    volume = fields.Float('Volume', copy=False)
    total_cbm = fields.Float('Total CBM')
    weight_st = fields.Float(digits_compute=dp.get_precision('Stock Weight'))
    weight_net_st = fields.\
        Float(digits_compute=dp.get_precision('Stock Weight'))
    weight = fields.Float('Weight', compute='_cal_weight', multi=True, readonly=False,
                          digits_compute=dp.get_precision('Stock Weight'))
    weight_net = fields.Float('Net Weight', compute="_cal_weight", readonly=False,
                              digits_compute=dp.get_precision('Stock Weight'),
                              multi=True)
    carrier_tracking_ref = fields.Char('Carrier Tracking Ref', copy=False)
    number_of_packages = fields.Integer('Number of Packages', copy=False)
    weight_uom_id = fields.Many2one('product.uom', 'Unit of Measure',
                                    required=True, readonly="1",
                                    help="Unit of measurement for Weight",
                                    default=_get_default_uom)
    carrier_name = fields.Char("Carrier name")
    carrier_service = fields.Char("Carrier service")


class StockMove(models.Model):

    _inherit = "stock.move"

    @api.multi
    @api.depends('product_id', 'product_uom_qty', 'product_uom', 'weight_st',
                 'weight_net_st')
    def _cal_move_weight(self):
        for move in self:
            weight = weight_net = 0.00
            if move.product_id.weight > 0.00:
                converted_qty = move.product_qty
                weight = (converted_qty * move.product_id.weight)

                if move.product_id.weight_net > 0.00:
                    weight_net = (converted_qty * move.product_id.weight_net)
            if move.weight_st:
                weight = move.weight_st
            if move.weight_net_st:
                weight_net = move.weight_net_st
            move.weight = weight
            move.weight_net = weight_net

    @api.model
    def _get_default_uom(self):
        uom_categ_id = self.env.ref('product.product_uom_categ_kgm')
        return self.env['product.uom'].search([('category_id', '=',
                                                uom_categ_id.id),
                                               ('factor', '=', 1)])[0]

    weight = fields.Float('Weight', compute='_cal_move_weight', multi=True,
                          digits_compute=dp.get_precision('Stock Weight'),
                          store=True, readonly=False)
    weight_net = fields.Float('Net weight', compute='_cal_move_weight',
                              digits_compute=dp.get_precision('Stock Weight'),
                              store=True, multi=True, readonly=False)
    weight_st = fields.Float(digits_compute=dp.get_precision('Stock Weight'))
    weight_net_st = fields.\
        Float(digits_compute=dp.get_precision('Stock Weight'))
    weight_uom_id = fields.Many2one('product.uom', 'Unit of Measure',
                                    required=True, readonly="1",
                                    help="Unit of Measure (Unit of Measure) "
                                         "is the unit of measurement for "
                                         "Weight", default=_get_default_uom)

    @api.multi
    def write(self, vals):
        if 'weight' in vals:
            vals['weight_st'] = vals.get('weight')
        if 'weight_net' in vals:
            vals['weight_net_st'] = vals.get('weight_net')
        return super(StockMove, self).write(vals)
