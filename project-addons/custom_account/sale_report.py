

from openerp import tools
from openerp.osv import fields, osv

class sale_report(osv.osv):
    _inherit = "sale.report"

    _columns = {
        'benefit': fields.float('Benefit', readonly=True),
        'cost_price': fields.float('Cost Price', readonly=True)
    }

    def _select(self):
        select_str = """
             SELECT min(l.id) as id,
		            sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) / 100.0) - (l.purchase_price*l.product_uom_qty) as benefit,
                    (l.purchase_price*l.product_uom_qty) as cost_price,
		            l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) / 100.0) as price_total,
                    count(*) as nbr,
                    s.date_order as date,
                    s.date_confirm as date_confirm,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_confirm)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    l.state,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    s.project_id as analytic_account_id,
                    s.section_id as section_id
        """
        return select_str

    def _from(self):
        from_str = """
                sale_order_line l
                      join sale_order s on (l.order_id=s.id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
                    (l.purchase_price*l.product_uom_qty),
                    l.product_id,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,
                    s.date_order,
                    s.date_confirm,
                    s.partner_id,
                    s.user_id,
                    s.company_id,
                    l.state,
                    s.pricelist_id,
                    s.project_id,
                    s.section_id
        """
        return group_by_str
