

from odoo import models, fields, api
from odoo import tools


class SaleReport(models.Model):
    _inherit = 'sale.report'

    _columns = {
        'benefit': fields.float('Benefit', readonly=True),
        'cost_price': fields.float('Cost Price', readonly=True)
    }

    def _select(self):
        select_str = super(SaleReport, self)._select()
        this_str = \
            """,sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) /
             100.0) - sum(l.purchase_price*l.product_uom_qty)
            as benefit, sum(l.purchase_price*l.product_uom_qty)
            as cost_price"""
        return select_str + this_str

    def _where(self):
        where_str = "l.deposit = false and l.pack_depth = 0 "
        return where_str

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            WHERE %s
            %s
            )""" % (self._table, self._select(), self._from(), self._where(),
                    self._group_by()))
