# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos S.L.
#    $Omar Castiñeira Saavedra$ <omar@comunitea.com>
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

from openerp import api, models, fields


class StockMove(models.Model):

    _inherit = "stock.move"

    @api.model
    def create(self, vals):
        move = super(StockMove, self).create(vals)
        if vals.get('state', False) != "draft":
            move.product_id._calc_remaining_days()
        return move

    @api.multi
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if vals.get('state', False):
            for move in self:
                move.product_id._calc_remaining_days()
        return res
