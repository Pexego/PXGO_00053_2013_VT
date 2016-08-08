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

from openerp import models, fields
import openerp.addons.decimal_precision as dp


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    qty_available = fields.\
        Float('Qty available', readonly=True,
              related='product_id.virtual_stock_conservative',
              digits_compute=dp.get_precision('Product Unit of Measure'))
    qty_available_wo_wh = fields.\
        Float('Qty. on kitchen', readonly=True,
              related='product_id.qty_available_wo_wh',
              digits_compute=dp.get_precision('Product Unit of Measure'))
    incoming_qty = fields.\
        Float('Incoming qty.', readonly=True,
              related='product_id.incoming_qty',
              digits_compute=dp.get_precision('Product Unit of Measure'))
