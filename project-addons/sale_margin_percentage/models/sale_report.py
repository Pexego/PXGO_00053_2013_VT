from odoo import models, fields, api
from odoo import tools


class SaleReport(models.Model):
    _inherit = 'sale.report'

    # benefit = fields.Float('Benefit', readonly=True),
    cost_price = fields.Float('Cost Price', readonly=True)

    def _select(self):
        select_str = super(SaleReport, self)._select()
        this_str = \
            """,sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) /
             100.0) - sum(l.purchase_price*l.product_uom_qty)
            as benefit, sum(l.purchase_price*l.product_uom_qty)
            as cost_price"""
        return select_str + this_str

    def _where(self):
        where_str = " "# TODO: migrar stock_deposit l.deposit = false"
        return where_str

