# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2013 Camptocamp SA
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

from odoo import models, fields


class stock_reservation(models.Model):
    _inherit = 'stock.reservation'

    sale_line_id = fields.Many2one(
            'sale.order.line',
            string='Sale Order Line',
            ondelete='cascade')
    sale_id = fields.Many2one("sale.order", related='sale_line_id.order_id',
                              string='Sale Order', readonly=True)
    partner_id = fields.Many2one("res.partner", related='sale_line_id.order_id.partner_id',
                                 string="Partner", readonly=True)
    user_id = fields.Many2one("res.users", related='sale_line_id.order_id.user_id',
                              string="Responsible", readonly=True)
    date_order = fields.Datetime(related='sale_line_id.order_id.date_order',
                                 string="Date order", readonly=True)

    def release(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'sale_line_id': False}, context=context)
        return super(stock_reservation, self).release(
            cr, uid, ids, context=context)

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default['sale_line_id'] = False
        return super(stock_reservation, self).copy_data(
            cr, uid, id, default=default, context=context)
