# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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

from openerp import fields, models, api

class sale_order_line(models.Model):

    _inherit = 'sale.order.line'

    unique_js_id = fields.Char('', size=64)
    temp_unique_js_id = fields.Char('', size=64)
    warehouse_id = fields.Many2one('stock.warehouse', 'warehouse', related='order_id.warehouse_id')

    @api.multi
    def write(self, vals):
        for line in self:
            unique_js_id = vals.get('unique_js_id', line.unique_js_id)
            temp_unique_js_id = vals.get('temp_unique_js_id', line.temp_unique_js_id)
            if temp_unique_js_id:
                if unique_js_id:
                    reserve_to_delete = self.env['stock.reservation'].search(
                        [('unique_js_id', '=', unique_js_id)])
                    reserve_to_delete.unlink()
                new_reserv = self.env['stock.reservation'].search(
                    [('unique_js_id', '=', temp_unique_js_id)])
                new_reserv.sale_line_id = line.id
                vals['unique_js_id'] = temp_unique_js_id
                vals['temp_unique_js_id'] = ''
        return super(sale_order_line, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('temp_unique_js_id', False):
            vals['unique_js_id'] = vals['temp_unique_js_id']
            vals.pop('temp_unique_js_id', None)
            res = super(sale_order_line, self).create(vals)
            reserve = self.env['stock.reservation'].search(
                [('unique_js_id', '=', res.unique_js_id)])
            reserve.sale_line_id = res.id
        else:
            res = super(sale_order_line, self).create(vals)
        return res

    @api.multi
    def unlink(self):
        for line in self:
            if line.unique_js_id:
                reserve = self.env['stock.reservation'].search(
                [('unique_js_id', '=', line.unique_js_id)])
                reserve.unlink()
            if line.temp_unique_js_id:
                reserve = self.env['stock.reservation'].search(
                [('unique_js_id', '=', line.temp_unique_js_id)])
                reserve.unlink()
        return super(sale_order_line,self).unlink()
