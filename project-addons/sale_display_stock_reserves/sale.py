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
from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    def _get_qty_reserved(self, cr, uid, ids, field_name, arg,
                                  context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = 0.0
            if line.product_id:
                result[line.id] = line.product_id.reserves_count
        return result
    
    _columns = {
        'qty_reserved': fields.function(_get_qty_reserved,
                                     string='Qty reserved', readonly=True,
                                     type="float",
                                     digits_compute=
                                     dp.get_precision('Product Unit \
                                                      of Measure'))
    }
