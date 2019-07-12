# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, tools


class StockHistory(models.Model):
    _name = 'stock.history'
    _auto = False
    _order = 'date asc'

    move_id = fields.Many2one('stock.move', 'Stock Move', readonly=True)
    location_id = fields.Many2one('stock.location', 'Location', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    quantity = fields.Float('Product Quantity', readonly=True)
    date = fields.Datetime('Operation Date', readonly=True)
    source = fields.Char('Source', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'stock_history')
        self._cr.execute("""
            CREATE OR REPLACE VIEW stock_history AS (
              SELECT MIN(id) as id,
                move_id,
                location_id,
                company_id,
                product_id,
                SUM(quantity) as quantity,
                date,
                source
                FROM
                ((SELECT
                    stock_move.id AS id,
                    stock_move.id AS move_id,
                    dest_location.id AS location_id,
                    dest_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    stock_move.product_uom_qty AS quantity,
                    stock_move.date AS date,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                   stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE stock_move.product_uom_qty>0 AND stock_move.state = 'done' AND dest_location.usage in ('internal', 'transit')
                  AND (
                    not (source_location.company_id is null and dest_location.company_id is null) or
                    source_location.company_id != dest_location.company_id or
                    source_location.usage not in ('internal', 'transit'))
                ) UNION ALL
                (SELECT
                    (-1) * stock_move.id AS id,
                    stock_move.id AS move_id,
                    source_location.id AS location_id,
                    source_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    - stock_move.product_uom_qty AS quantity,
                    stock_move.date AS date,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE stock_move.product_uom_qty>0 AND stock_move.state = 'done' AND source_location.usage in ('internal', 'transit')
                 AND (
                    not (dest_location.company_id is null and source_location.company_id is null) or
                    dest_location.company_id != source_location.company_id or
                    dest_location.usage not in ('internal', 'transit'))
                ))
                AS foo
                GROUP BY move_id, location_id, company_id, product_id, date, source HAVING SUM(quantity) != 0
            )""")


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
