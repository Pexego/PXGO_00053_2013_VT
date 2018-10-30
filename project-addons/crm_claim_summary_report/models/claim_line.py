# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 Comunitea Servicios Tecnológicos S.L.
#    Author : Omar Castiñeira Saavedra <omar@comunitea.com>
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

from openerp import models, fields


class ClaimLine(models.Model):

    _inherit = "claim.line"

    printable = fields.Boolean("Printable", default=True)

    claim_origine = fields.Selection([('broken_down', 'Broken down product'),
         ('not_appropiate', 'Not appropiate product'),
         ('cancellation', 'Order cancellation'),
         ('damaged', 'Damaged delivered product'),
         ('error', 'Shipping error'),
         ('exchange', 'Exchange request'),
         ('lost', 'Lost during transport'),
         ('other', 'Other')
         ],
        'Claim Subject',
        required=True,
        help="To describe the line product problem")