# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
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
import openerp
from openerp import tools
from openerp.osv import osv, fields


class res_partner(osv.osv):
    _inherit = 'res.partner'

    def _get_image(self, cr, uid, ids, name, args, context=None):
        """ """
        result = dict.fromkeys(ids, False)
        for partner in self.browse(cr, uid, ids, context=context):
            if partner.mood_image and partner.mood_image.image_small:
                result[partner.id] = partner.mood_image.image_small
        return result

    _columns = {
        'mood_image': fields.many2one('mood', 'Mood'),
        'selected_image': fields.function(_get_image, string="Mood",
                                          type="binary"),
    }
