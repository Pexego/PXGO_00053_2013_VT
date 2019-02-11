##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
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

from odoo import models, api, fields, exceptions, _


class QualityMoveWzd(models.TransientModel):

    _name = "quality.move.wzd"

    qty = fields.Float('Qty. to move', default=1.0, required=True)

    @api.multi
    def action_move(self):
        move_obj = self.env["stock.move"]
        move = move_obj.browse(self._context["active_id"])
        dest_location = self.env.ref("location_moves.stock_location_quality")
        if self[0].qty > move.product_uom_qty:
            raise exceptions.Warning(_("Cannot move more than origin move "
                                       "qty."))
        elif not move.picking_id:
            raise exceptions.Warning(_("Only can do this operation with "
                                       "picked moves"))
        elif move.picking_id.picking_type_code != "incoming":
            raise exceptions.Warning(_("Only can do this operation with "
                                       "incoming pickings"))
        elif move.location_id.usage not in ["supplier", "production"]:
            raise exceptions.Warning(_("Only can do this operation with "
                                       "incoming pickings"))
        if self[0].qty == move.product_uom_qty:
            move.location_dest_id = dest_location.id
        else:
            new_move = move.copy({'product_uom_qty': self[0].qty,
                                  'location_dest_id': dest_location.id,
                                  'state': move.state})
            move.product_uom_qty -= self[0].qty
            move.picking_id.action_assign()
            new_move.action_done()
        return True
