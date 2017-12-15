# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
from openerp import models, fields, tools


class stock_days_positive(models.Model):

    _name = 'stock.days.positive'
    _auto = False

    product_id = fields.Many2one('product.product', 'Product')
    qty = fields.Float('Quantity')
    datum = fields.Date('Date')

    def init(self, cr):
        warehouse_obj = self.pool["stock.warehouse"]
        location_ids = []
        warehouse_ids = warehouse_obj.search(cr, 1, [])
        for warehouse in warehouse_obj.browse(cr, 1, warehouse_ids):
            location_ids.append(warehouse.view_location_id.id)
        tools.drop_view_if_exists(cr, 'stock_days_positive')
        cr.execute(
            """
            CREATE OR REPLACE VIEW stock_days_positive as (
            SELECT EXTRACT(EPOCH from datum) || '' || product_id as id, product_id, SUM(quantity) AS qty,datum
            FROM stock_history,
                (SELECT NOW()::DATE - sequence.day AS datum
                 FROM generate_series(0,200) AS sequence(day)
                 GROUP BY sequence.day
                 ORDER BY datum desc) as dates
            WHERE location_id IN (SELECT id FROM stock_location WHERE usage = 'internal' and location_id in (%s))
                AND stock_history.date::DATE <= (dates.datum || ' 23:59:59')::DATE
            GROUP BY product_id,datum
            HAVING sum(quantity) > 0)
            """ % tuple(location_ids))


class stock_history(models.Model):
    _inherit = 'stock.history'


    def init(self, cr):
        """
            En un update all se inicia 2 veces esta vista, la 2º vez al
            eliminarla elimina tambien stock_days, por lo que tenemos que
            forzarlo para iniciarla de nuevo
        """
        res = super(stock_history,self).init(cr)
        self.pool['stock.days.positive'].init(cr)
        return res
