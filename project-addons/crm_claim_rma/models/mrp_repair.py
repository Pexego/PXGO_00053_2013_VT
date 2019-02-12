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

from odoo import models, fields, api


class MrpRepair(models.Model):

    _inherit = "mrp.repair"

    @api.one
    @api.depends('claim_line_ids')
    def _get_claim_id(self):
        if self.claim_line_ids:
            self.claim_id = self.claim_line_ids[0].claim_id.id
        else:
            self.claim_id = False

    claim_id = fields.Many2one("crm.claim", "Claim", compute=_get_claim_id,
                               readonly=True, store=True)
    claim_line_ids = fields.One2many('claim.line', 'repair_id', 'Claims',
                                     readonly=True)
