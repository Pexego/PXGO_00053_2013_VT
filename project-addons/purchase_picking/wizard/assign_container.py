##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos S.L.
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

class AssignContainerWzd(models.TransientModel):

    _name = "assign.container.wzd"

    container_id = fields.Many2one("stock.container", "Container",
                                   required=True)

    @api.multi
    def action_assign(self):
        move_obj = self.env["stock.move"]
        for move in move_obj.browse(self.env.context["active_ids"]):
            move.container_id = self[0].container_id.id
        return {}
