# -*- coding: utf-8 -*-
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
from openerp import models, SUPERUSER_ID

class stock_move(models.Model):

    _inherit = 'stock.move'

    def product_price_update_before_done(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('product.product')
        for move in self.browse(cr, uid, ids, context=context):
            #adapt standard price on incomming moves if the product cost_method is 'average'
            if (move.location_id.usage == 'supplier') and (move.product_id.cost_method == 'average'):
                product = move.product_id
                product_avail = product.qty_available
                if product.qty_available <= 0:
                    new_std_price = move.price_unit
                else:
                    # Get the standard price
                    amount_unit = product.standard_price
                    new_std_price = ((amount_unit * product_avail) + (move.price_unit * move.product_qty)) / (product_avail + move.product_qty)
                    new_std_price_cost = ((product.standard_price_cost * product_avail) + (move.price_unit * move.product_qty)) / (product_avail + move.product_qty)
                # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
                product_obj.write(cr, SUPERUSER_ID, [product.id], {'standard_price': new_std_price, 'standard_price_cost': new_std_price_cost}, context=context)
