# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
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

from openerp import models, fields, api


class StockMove(models.Model):

    _inherit = "stock.move"

    tests = fields.Boolean("Tests", readonly=True)

    @api.model
    def _prepare_picking_assign(self, move):
        vals = super(StockMove, self)._prepare_picking_assign(move)
        vals['tests'] = move.tests
        return vals

    @api.model
    def _prepare_procurement_from_move(self, move):
        vals = super(StockMove, self)._prepare_procurement_from_move(move)
        vals['tests'] = move.tests
        return vals


class StockPicking(models.Model):

    _inherit = "stock.picking"

    tests = fields.Boolean("Tests", readonly=True)
