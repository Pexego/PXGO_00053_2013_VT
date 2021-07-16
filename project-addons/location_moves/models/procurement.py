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
import logging

_logger = logging.getLogger(__name__)


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def run_scheduler_internal_pickings(self):
        max_commit_len = int(self.env['ir.config_parameter'].sudo().get_param('max_commit_len'))
        _logger.info("CHECKING AVAILABILITY")
        pickings_to_check = self.env['stock.picking'].search([('picking_type_id', '=', self.env.ref('stock.picking_type_internal').id),
                                                ('state', 'in', ['confirmed', 'partially_available'])])
        len_pickings_to_check = len(pickings_to_check)
        pickings_commit = self.env['stock.picking']
        for count, pick_to_check in enumerate(pickings_to_check):
            pick_to_check.action_assign()
            pickings_commit += pick_to_check
            pick_number = count + 1
            if (pick_number >= max_commit_len and pick_number % max_commit_len == 0) or pick_number == len_pickings_to_check:
                self.env.cr.commit()
                _logger.info("COMMIT DONE: %s" % pickings_commit)
                pickings_commit = self.env['stock.picking']


        _logger.info("SEARCHING FOR INTERNAL PICKINGS")
        operation_internal = self.env.ref('stock.picking_type_internal').id
        transit_it_location = self.env['stock.location'].search([('name', '=', 'Tránsito Italia')]).id
        pick_ids_assign = self.env["stock.picking"]. \
            search([("picking_type_id", "=",
                     operation_internal),
                    ("state", "=", "assigned"),
                    ("location_id", "!=", transit_it_location)])

        pick_ids_confirmed = self.env["stock.picking"]. \
            search([("picking_type_id", "=",
                     operation_internal),
                    ("state", "=", "confirmed"), ('move_type', '!=', 'direct')])
        len_pick_assign = len(pick_ids_assign)

        _logger.info("TRANSFERRING READY INTERNAL PICKINGS")
        pickings_commit = self.env['stock.picking']
        for count, pick_assign in enumerate(pick_ids_assign):
            pick_assign.action_done()
            pickings_commit += pick_assign
            pick_number = count + 1
            if (pick_number >= max_commit_len and pick_number % max_commit_len == 0) or pick_number == len_pick_assign:
                self.env.cr.commit()
                _logger.info("COMMIT DONE: %s" %pickings_commit)
                pickings_commit = self.env['stock.picking']

        _logger.info("PROCESSING CONFIRMED AND PARTIALLY AVAILABLE PICKINGS")
        if pick_ids_confirmed:
            pick_ids_confirmed.write({'move_type': 'direct'})
        pick_ids_par = self.env["stock.picking"]. \
            search([("picking_type_id", "=",
                     operation_internal),
                    ("state", "=", "partially_available")])

        pick_ids_par.write({'move_type': 'direct'})
        pickings_commit = self.env['stock.picking']
        for count, pick_partially in enumerate(pick_ids_par):
            pick_partially.action_copy_reserv_qty()
            pick_partially.action_accept_confirmed_qty()
            pickings_commit += pick_partially
            pick_number = count + 1
            if (pick_number >= max_commit_len and pick_number % max_commit_len == 0) or pick_number == len(pick_ids_par):
                self.env.cr.commit()
                _logger.info("COMMIT DONE: %s" % pickings_commit)
                pickings_commit = self.env['stock.picking']
        _logger.info("DONE")
