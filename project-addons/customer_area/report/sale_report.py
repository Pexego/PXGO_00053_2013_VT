##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
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

from odoo import models, fields

class sale_report(models.Model):

    _inherit = 'sale.report'

    area_id = fields.Many2one('res.partner.area','Area')
    commercial_region_ids = fields.Many2many(related='area_id.commercial_region_ids')

    def _select(self):
        select_str = super(sale_report,self)._select()
        this_str = """, s.area_id as area_id"""
        return select_str + this_str


    def _group_by(self):
        group_by_str = super(sale_report,self)._group_by()
        this_str = """, s.area_id"""
        return group_by_str + this_str
