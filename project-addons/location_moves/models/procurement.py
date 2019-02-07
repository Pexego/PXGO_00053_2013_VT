# -*- coding: utf-8 -*-
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

from openerp import models, api

class ProcurementOrder(models.Model):

    _inherit = "procurement.order"

    @api.model
    def run_scheduler(self, use_new_cursor=False, company_id = False):
        res = super(ProcurementOrder, self).\
            run_scheduler(use_new_cursor=use_new_cursor,
                          company_id=company_id)
        pick_ids = self.env["stock.picking"].\
            search([("picking_type_code", "=", "internal"),
                    ("state", "=", "assigned")])
        for pick in pick_ids:
            pick.action_done()
        if use_new_cursor:
            self.env.cr.commit()

        return res
