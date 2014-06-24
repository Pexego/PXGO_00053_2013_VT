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


class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'customer_mood': fields.binary('Customer Mood', readonly=True)
    }

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        result = super(sale_order, self).onchange_partner_id(cr, uid, ids,
                                                             part, context)
        if part:
            part = self.pool.get('res.partner').browse(cr, uid, part,
                                                       context=context)
            if part.mood_image and part.mood_image.image:
                result['value']['customer_mood'] = part.mood_image.image_small
        return result
