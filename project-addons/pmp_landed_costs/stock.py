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

    def product_price_update_after_done(self, cr, uid, ids, context=None):
        #res = super(stock_move, self).product_price_update_after_done(cr, uid, ids, context)
        product_obj = self.pool.get('product.product')
        for move in self.browse(cr, uid, ids, context=context):
            if (move.location_id.usage == 'supplier') and (move.product_id.cost_method == 'real'):
                product_obj.update_real_cost(cr, uid, move.product_id.id, context)
        #return res

    def _store_average_cost_price(self, cr, uid, move, context=None):
        if (move.location_id.usage == 'supplier') and (move.product_id.cost_method == 'real'):
            return super(stock_move, self)._store_average_cost_price(cr, uid, move, context=context)
