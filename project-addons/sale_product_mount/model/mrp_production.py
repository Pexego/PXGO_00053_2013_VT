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
from openerp import models, api


class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    @api.one
    def action_assign(self):
        super(MrpProduction, self).action_assign()
        for move in self.move_lines:
            if move.state == 'confirmed':
                reserv_dict = {
                    'date_validity': False,
                    'name': u"{} ({})".format(self.name, move.name),
                    'mrp_id': self.id,
                    'move_id': move.id
                }
                reservation = self.env['stock.reservation'].create(reserv_dict)
                reservation.reserve()
