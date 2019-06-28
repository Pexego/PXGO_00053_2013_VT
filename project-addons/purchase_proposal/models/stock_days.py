# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, tools


class StockDaysPositive(models.Model):

    _name = 'stock.days.positive'
    _auto = False

    product_id = fields.Many2one('product.product', 'Product')
    qty = fields.Float('Quantity')
    datum = fields.Date('Date')

    def init(self):
        warehouse_obj = self.env["stock.warehouse"]
        location_ids = []
        warehouse_ids = warehouse_obj.search([])
        for warehouse in warehouse_ids:
            location_ids.append(warehouse.view_location_id.id)
        tools.drop_view_if_exists(self._cr, 'stock_days_positive')
        self._cr.execute(
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
