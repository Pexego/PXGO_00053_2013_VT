##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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


class ResPartner(models.Model):

    _inherit = 'res.partner'

    points_in_bag = fields.Integer(compute='_get_points', string='Points',
                                   readonly=True)

    @api.multi
    def _get_points(self):
        read_group_res = self.env['res.partner.point.programme.bag'].read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id','points'],
            ['partner_id'])
        mapped_data = {data['partner_id'][0]: data['points'] for data in read_group_res}
        for partner in self:
            partner.points_in_bag = mapped_data.get(partner.id, 0)
