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

    unique_js_id = fields.Char('', size=64, copy=False)
    temp_unique_js_id = fields.Char('', size=64, copy=False)

    @api.multi
    def write(self, vals):
        ctx = dict(self.env.context)
        for line in self:
            unique_js_id = vals.get('unique_js_id', line.unique_js_id)
            temp_unique_js_id = vals.get('temp_unique_js_id',
                                         line.temp_unique_js_id)

            if temp_unique_js_id:
                if vals.get('reservation_ids', False):
                    vals.pop('reservation_ids')
                if unique_js_id:
                    reserve_to_delete = self.env['stock.reservation'].search(
                        [('unique_js_id', '=', unique_js_id)])
                    if reserve_to_delete:
                        reserve_to_delete.unlink()
                elif line.reservation_ids:
                    line.reservation_ids.unlink()
                new_reserv = self.env['stock.reservation'].search(
                    [('unique_js_id', '=', temp_unique_js_id)])
                if new_reserv:
                    new_reserv.sale_line_id = line.id
                    new_reserv.origin = line.order_id.name
                else:
                    ctx['later'] = True
                vals['unique_js_id'] = temp_unique_js_id
                vals['temp_unique_js_id'] = ''
        return super(sale_order_line, self.with_context(ctx)).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('temp_unique_js_id', False):
            vals['unique_js_id'] = vals['temp_unique_js_id']
            vals.pop('temp_unique_js_id', None)
            res = super(sale_order_line, self).create(vals)
            reserve = self.env['stock.reservation'].search(
                [('unique_js_id', '=', res.unique_js_id)])
            if reserve:
                reserve.sale_line_id = res.id
                reserve.origin = res.order_id.name
        else:
            res = super(sale_order_line, self).create(vals)
        return res

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        if 'unique_js_id' in fields:
            reserv_obj = self.env['stock.reservation']
            for line in self:
                self._cr.execute("select sale_order.state, unique_js_id from "
                                 "sale_order_line inner join sale_order on "
                                 "sale_order.id = sale_order_line.order_id "
                                 "where sale_order_line.id = %s"
                                 % str(line.id))
                line_data = self._cr.fetchone()
                if line_data and line_data[0] == "reserve" and line_data[1]:
                    reserves = reserv_obj.search([('unique_js_id', '=',
                                                   line_data[1]),
                                                  ('state', '!=',
                                                   'cancel')])
                    while len(reserves) > 1:
                        reserv = reserves.pop()
                        reserv_obj.unlink(reserv)
                    if reserves and not reserves[0].sale_line_id:
                        reserves[0].sale_line_id = line.id
                        reserves[0].origin = line.order_id.name

        return super(sale_order_line, self).read(fields=fields, load=load)

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
        return super(sale_order_line, self).unlink()

    @api.multi
    def stock_reserve(self):
        if self.env.context.get('later', False):
            return True
        else:
            return super(sale_order_line, self).stock_reserve()
