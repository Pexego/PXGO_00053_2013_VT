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


class SaleOrder(models.Model):

    _inherit = "sale.order"

    tests = fields.Boolean("Tests", copy=False, readonly=True)

    @api.one
    def set_tests(self):
        self.tests = True
        for pick in self.picking_ids:
            pick.tests = True
            for move in pick.move_lines:
                move.tests = True
                if move.procurement_id:
                    move.procurement_id.tests = True

        return True

    @api.one
    def unset_tests(self):
        self.tests = False
        for pick in self.picking_ids:
            pick.tests = False
            for move in pick.move_lines:
                move.tests = False
                if move.procurement_id:
                    move.procurement_id.tests = False

        return True

    @api.model
    def _prepare_order_line_procurement(self, order, line, group_id=False):
        vals = super(SaleOrder, self).\
            _prepare_order_line_procurement(order, line, group_id=group_id)
        vals["tests"] = order.tests
        return vals
