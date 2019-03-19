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
        if not records:
            self.average_margin_last_sales()
            products = self.search([('type', '!=', 'service')])
            product_ids = products.ids
        else:
            product_ids = records
        for product_id in product_ids:
            self.env.cr.execute("select min(t.datum) from (select product_id,"
                                "datum from stock_days_positive where "
                                "product_id = %s order by datum desc "
                                "limit 60) as t" % (product_id))
            days_data = self.env.cr.fetchone()
            if days_data:
                product = self.browse(product_id)
                picking_type_ids = self.env['stock.picking.type'].search(
                    [('code', '=', 'outgoing')])

                moves = self.env['stock.move'].search(
                    [('date', '>=', days_data[0]),
                     ('state', '=', 'done'),
                     ('product_id', '=', product.id),
                     ('picking_type_id', 'in', picking_type_ids.ids),
                     ('sale_line_id', '!=', False)])
                biggest_move_qty = 0.0
                biggest_order = False
                qty = 0.0
                for move in moves:
                    qty += move.product_uom_qty
                    if move.product_uom_qty > biggest_move_qty:
                        biggest_move_qty = move.product_uom_qty
                        biggest_order = \
                            move.sale_line_id.order_id.id

                vals = {'last_sixty_days_sales': qty,
                        'biggest_sale_qty': biggest_move_qty,
                        'biggest_sale_id': biggest_order}

                product.write(vals)

    @api.model
    def average_margin_last_sales(self, ids=False):
        if not ids:
            sql_sentence = """
                SELECT DISTINCT product_id
                    FROM sale_order_line
                    WHERE state not in ('draft', 'cancel', 'exception')
                    AND product_id IS NOT NULL
            """
            self.env.cr.execute(sql_sentence)
            res = self.env.cr.fetchall()
            product_ids = [x[0] for x in res]
        else:
            product_ids = ids
        for product_id in self.browse(product_ids):
            sale_lines = self.env['sale.order.line'].search(
                [('product_id', '=', product_id.id),
                 ('state', 'not in',
                 ('draft', 'cancel', 'exception'))],
                limit=100,
                order='date_order desc')
            margin_perc_sum = 0
            qty_sum = 0
            for line in sale_lines:
                margin_perc_sum += (line.margin_perc * line.product_uom_qty)
                qty_sum += line.product_uom_qty
            if qty_sum:
                product_id.average_margin = margin_perc_sum / qty_sum

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
