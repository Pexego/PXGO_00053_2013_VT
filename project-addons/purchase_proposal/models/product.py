# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.depends("history_ids")
    def _compute_pvm_price(self):
        pricelist = self.env['product.pricelist'].search(
            [('name', '=', 'PVM')], limit=1)
        if pricelist:
            for product in self:
                product.pvm_price = product.with_context(
                    pricelist=pricelist.id).price
                # este campo es calculado y nos devuelve el
                # precio del prodiucto según la tarifa
                # en contexto, acepta también otros parámetros
        else:
            for product in self:
                product.pvm_price = 0.0

    history_ids = fields.One2many('product.price.history', 'product_id')
    pvm_price = fields.Float("PVM Price", store=True,
                             compute='_compute_pvm_price')
    last_sixty_days_sales = fields.Float('Sales in last 60 days with stock',
                                         readonly=True)
    biggest_sale_qty = fields.Float(readonly=True, digits=(16, 2))
    biggest_sale_id = fields.Many2one("sale.order", "Biggest order",
                                      readonly=True)
    order_cycle = fields.Integer()
    transport_time = fields.Integer()
    security_margin = fields.Integer()
    average_margin = fields.Float("Average Margin Last Sales", readonly=True)
    ref_manufacturer = fields.Char(related='manufacturer_pref', readonly=True)

    @api.model
    def compute_last_sixty_days_sales(self, records=False):
        query = """select pp.id,(select sum(product_uom_qty) from stock_move
    sm inner join stock_picking_type spt on spt.id = sm.picking_type_id inner
    join procurement_order po on po.id = sm.procurement_id where date >=
    (select min(t.datum) from (select product_id,datum from stock_days_positive
    where product_id = pp.id order by datum desc limit 60) as t) and
    sm.state = 'done' and sm.product_id = pp.id and spt.code = 'outgoing' and
    po.sale_line_id is not null), (select min(t2.datum) from (select product_id,
    datum from stock_days_positive where product_id = pp.id order by datum desc
    limit 60) as t2) from product_product pp inner join product_template pt on
    pt.id = pp.product_tmpl_id where pt.type != 'service'"""
        picking_type_obj = self.env['stock.picking.type']
        picking_type_ids = picking_type_obj.search([('code', '=', 'outgoing')])
        if not records:
            self.average_margin_last_sales()
        else:
            query += " and pp.id in (%s) " % \
                     ",".join([str(x) for x in records])
        move_obj = self.env['stock.move']
        self._cr.execute(query)
        data = self._cr.fetchall()
        for product_data in data:
            if product_data[1]:
                moves = move_obj.search([('date', '>=', product_data[2]),
                                         ('state', '=', 'done'),
                                         ('product_id', '=', product_data[0]),
                                         ('picking_type_id', 'in',
                                          picking_type_ids.ids),
                                         ('procurement_id.sale_line_id', '!=',
                                          False)],
                                        order="product_uom_qty desc", limit=1)
                biggest_move_qty = moves[0].product_uom_qty
                biggest_order = \
                    moves[0].procurement_id.sale_line_id.order_id.id
                self._cr.execute("update product_product set biggest_sale_id ="
                                 " %s, biggest_sale_qty = %s, "
                                 "last_sixty_days_sales = %s where id = %s" %
                                 (biggest_order, biggest_move_qty,
                                  product_data[1], product_data[0]))
            else:
                self._cr.execute("update product_product set biggest_sale_id ="
                                 " null, biggest_sale_qty = %s, "
                                 "last_sixty_days_sales = %s where id = %s" %
                                 (0.0, 0.0, product_data[0]))

    @api.model
    def average_margin_last_sales(self, ids=False):
        query = """select id, (select case when sum(product_uom_qty) > 0
    then sum(margin_perc * product_uom_qty) / sum(product_uom_qty) else 0.0 end
    from (select * from sale_order_line where state not in ('draft', 'cancel',
    'exception') and product_id = product_product.id order by date_order desc
    limit 100) as t) from product_product"""
        if ids:
            query += " where id in (%s) " % ",".join([str(x) for x in ids])
        self._cr.execute(query)



        data = self._cr.fetchall()
        for product_data in data:
            if product_data[1]:
                self._cr.execute("update product_product set average_margin = "
                                 "%s where id = %s" %
                                 (product_data[1], product_data[0]))

    @api.multi
    def average_margin_compute(self):
        self.average_margin_last_sales(ids=self.ids)

    @api.multi
    def action_compute_last_sixty_days_sales(self):
        self.compute_last_sixty_days_sales(records=self.ids)


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.depends('order_id', 'order_id.date_order')
    def _compute_date_order(self):
        for line in self:
            if line.order_id:
                line.date_order = line.order_id.date_order
            else:
                line.date_order = False

    date_order = fields.Date("Date", readonly=True, store=True,
                             compute="_compute_date_order")
