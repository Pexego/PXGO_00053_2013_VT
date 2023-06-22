from odoo import models, fields, tools
from odoo.addons import decimal_precision as dp


class StockDepositReport(models.Model):
    _name = 'stock.deposit.report'
    _description = 'Stock Deposit Report'
    _auto = False
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_qty = fields.Float(
        'Qty.', readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))
    owner_id = fields.Many2one('res.partner', "Owner", readonly=True)
    location_id = fields.Many2one('stock.location', "Location", readonly=True)
    company_id = fields.Many2one('res.company', "Company", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            """CREATE OR REPLACE VIEW %s AS (
                SELECT max(sq.id) as id, product_id,
                sum(quantity) as product_qty, owner_id, sq.location_id,
                sl.company_id from stock_quant sq
                inner join stock_location sl on sq.location_id=sl.id
                where sl.usage in ('internal', 'transit') and
                owner_id is not null
                group by product_id, owner_id, sq.location_id,
                sl.company_id)""" %
            (self._table))
