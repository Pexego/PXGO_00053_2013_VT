##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from odoo import models, fields, tools


class SaleOrderLineReport(models.Model):

    _name = 'sale.order.line.report'
    _auto = False
    _order = 'date_order desc'

    name = fields.Char('Name', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_brand_id = fields.Many2one('product.brand', 'Brand')
    product_category_id = fields.Many2one('product.category', 'Category', readonly=True)
    product_state = fields.Selection([
        ('draft', 'In Development'),
        ('sellable', 'Normal'),
        ('end', 'End of Lifecycle'),
        ('obsolete', 'Obsolete'),
        ('make_to_order', 'Make to order')],
        'Product state', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    country_id = fields.Many2one('res.country', 'Partner country', readonly=True)
    product_qty = fields.Float('Quantity', readonly=True)
    price_unit = fields.Float('Price unit', readonly=True)
    discount = fields.Float('Discount', readonly=True)
    qty_delivered = fields.Float('Qty delivered', readonly=True)
    salesman_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    order_id = fields.Many2one('sale.order', 'Order', readonly=True)
    team_id = fields.Many2one('crm.team', 'Order team', readonly=True)
    date_order = fields.Datetime('Dateorder', readonly=True)
    confirmation_date = fields.Datetime('Confirmationdate', readonly=True)
    invoice_status = fields.Selection([
        ('upselling', 'Upselling'),
        ('invoiced', 'Invoiced'),
        ('to invoice', 'To invoice'),
        ('no', 'Nothing to invoice'),
        ('cancel', 'Cancel')
        ],
        'Line invoice status', readonly=True)
    order_state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('reserve', 'Reserved'),
        ('sale', 'Sales Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('history', 'History')
        ],
        'Order state', readonly=True)
    invoice_status_2 = fields.Selection([
        ('invoiced', 'Fully Invoiced'),
        ('to_invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice'),
        ('partially_invoiced', 'Partially invoiced')
        ],
        'Order invoice status', readonly=True)
    incoming_qty = fields.Float('Incoming', related='product_id.incoming_qty')
    qty_available = fields.Float('Real Stock', related='product_id.qty_available')
    company_id = fields.Many2one("res.company", "Company", readonly=True)
    qty_pending = fields.Float('Qty Pending', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
CREATE or REPLACE VIEW sale_order_line_report as (SELECT sol.id as id,
       sol.name as name,
       sol.product_id as product_id,
       pt.product_brand_id as product_brand_id,
       pt.categ_id as product_category_id,
       pt.state as product_state,
       sol.order_partner_id as partner_id,
       rp.country_id as country_id,
       sol.product_uom_qty as product_qty,
       sol.price_unit as price_unit,
       sol.discount as discount,
       sol.qty_delivered as qty_delivered,
       sol.salesman_id as salesman_id,
       sol.invoice_status as invoice_status,
       sol.order_id as order_id,
       so.date_order as date_order,
       so.confirmation_date as confirmation_date,
       so.team_id as team_id,
       so.state as order_state,
       so.invoice_status_2 as invoice_status_2,
       sol.company_id as company_id,
       sol.product_uom_qty - sol.qty_delivered as qty_pending
FROM   sale_order_line sol
JOIN sale_order so on so.id = sol.order_id
LEFT JOIN product_product pp on sol.product_id = pp.id
LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
LEFT JOIN stock_move sm on sm.sale_line_id = sol.id
LEFT JOIN res_partner rp on rp.id = sol.order_partner_id
GROUP BY sol.id, sol.name, pt.product_brand_id, pt.categ_id, sol.order_partner_id, rp.country_id, sol.product_uom_qty,
         sol.product_uom, sol.price_unit, sol.discount, sol.salesman_id, sol.state, sol.order_id,
         so.date_order, so.confirmation_date, so.team_id, pt.state, so.state, so.invoice_status_2)
""")
