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

from odoo import models, api
from odoo.tools.profiler import profile


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    @profile
    def _run_scheduler_tasks(self, use_new_cursor=False, company_id=False):
        super()._run_scheduler_tasks(use_new_cursor=use_new_cursor,
                                     company_id=company_id)
        pick_ids = self.env["stock.picking"].\
            search([("picking_type_id", "=",
                     self.env.ref('stock.picking_type_internal').id),
                    ("state", "in", ("assigned", "confirmed", "partially_available"))])
        for picking in pick_ids:
            if picking.state == "assigned":
                picking.action_done()
            elif picking.state in ("confirmed", "partially_available"):
                picking.move_type = 'direct'
                if picking.state == "partially_available":
                    picking.action_copy_reserv_qty()
                    picking.action_accept_confirmed_qty()

        # Merge both crons to avoid overlap
        self.env['stock.reservation'].delete_orphan_reserves()

        if use_new_cursor:
            self.env.cr.commit()
