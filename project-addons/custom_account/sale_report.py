

from openerp.osv import fields, osv


class sale_report(osv.osv):
    _inherit = "sale.report"

    _columns = {
        'benefit': fields.float('Benefit', readonly=True),
        'cost_price': fields.float('Cost Price', readonly=True)
    }

    def _select(self):
        select_str = super(sale_report, self)._select()
        this_str = \
            """,sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) /
             100.0) - sum(l.purchase_price*l.product_uom_qty)
            as benefit, sum(l.purchase_price*l.product_uom_qty)
            as cost_price"""
        return select_str + this_str
