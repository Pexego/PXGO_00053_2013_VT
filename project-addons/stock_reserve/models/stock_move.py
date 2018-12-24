# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from odoo import models, api


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        objs = super(stock_move, self).search(args, offset=offset, limit=limit,
                                              order=order, count=count)
        reserv_obj = self.env['stock.reservation']
        reserve_ids = reserv_obj.search_read([('move_id', 'in', objs.ids)],
                                             ['move_id'], order='sequence asc')
        ordered_ids = [x['move_id'][0] for x in reserve_ids]
        ordered_data = self.browse(ordered_ids)
        not_ordered = objs - ordered_data
        ids = not_ordered + ordered_data

        return ids
