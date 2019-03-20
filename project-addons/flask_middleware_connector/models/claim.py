##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from odoo import models, fields, api, exceptions, _


class ClaimLine(models.Model):

    _inherit = 'claim.line'

    date_in = fields.Datetime('')
    date_out = fields.Datetime('')
    web = fields.Boolean('Web', default=True)

    @api.multi
    def write(self, vals):
        delete = True
        if vals.get('web', False):
            for record in self:
                if record.web != vals['web']:
                    delete = False
                    break
            if delete:
                del vals['web']
        return super(ClaimLine, self).write(vals)
