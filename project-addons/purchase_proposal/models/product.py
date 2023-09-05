# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


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
    average_margin = fields.Float("Average Margin Last Sales", readonly=True, copy=False)
    ref_manufacturer = fields.Char(related='manufacturer_pref', readonly=True)

    rotation_index = fields.Selection([(1, 'A'), (2, 'B'), (3, 'C')], string="Rotation")

    @api.model
    def compute_last_sixty_days_sales(self, records=False):
        country_code = self.env.user.company_id.country_id.code
        move_obj = self.env['stock.move']
        picking_type_obj = self.env['stock.picking.type']
        picking_type_ids = picking_type_obj.search([('code', '=', 'outgoing')])
        location_customer = self.env.ref('stock.stock_location_customers')
        if country_code == 'ES':
            query = """
                        select pp.id,
                               (select sum(sm.product_uom_qty)
                                from stock_move sm
                                inner join stock_picking_type spt on spt.id = sm.picking_type_id
                                inner join procurement_group po on po.id = sm.group_id
                                where date >= (select min(t.datum)
                                               from (select product_id, datum
                                                     from stock_days_positive
                                                     where product_id = pp.id
                                                     order by datum desc limit 60) as t)
                                      and sm.state = 'done' and sm.product_id = pp.id and spt.code = 'outgoing'
                                      and po.sale_id is not null and sm.location_dest_id = {}),
                                (select min(t2.datum) from (select product_id, datum
                                                            from stock_days_positive
                                                            where product_id = pp.id
                                                            order by datum desc
                                                            limit 60) as t2)
                        from product_product pp inner join product_template pt on pt.id = pp.product_tmpl_id
                        where pt.type != 'service'
                    """.format(location_customer.id)
            if not records:
                self.average_margin_last_sales()
            else:
                query += " and pp.id in (%s) " % \
                         ",".join([str(x) for x in records])
            self._cr.execute(query)
            data = self._cr.fetchall()
            for product_data in data:
                if product_data[1]:
                    moves = move_obj.search([('date', '>=', product_data[2]),
                                             ('state', '=', 'done'),
                                             ('product_id', '=', product_data[0]),
                                             ('picking_type_id', 'in',
                                              picking_type_ids.ids),
                                             ('group_id.sale_id', '!=',
                                              False)],
                                            order="product_uom_qty desc", limit=1)
                    biggest_move_qty = moves[0].product_uom_qty
                    biggest_order = \
                        moves[0].group_id.sale_id.id
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
        else:
            now = datetime.now()
            last_sixty_days = (now - relativedelta(days=60)).strftime("%Y-%m-%d")
            products = self.env['product.product'].search([('type', '!=', 'service')])
            if not records:
                self.average_margin_last_sales()
            else:
                products = products.filtered(lambda x: x.id in records)
            for product in products:
                moves = move_obj.search([('date', '>=', last_sixty_days),
                                         ('state', '=', 'done'),
                                         ('product_id', '=', product.id),
                                         ('picking_type_id', 'in', picking_type_ids.ids),
                                         ('group_id.sale_id', '!=', False),
                                         ('location_dest_id', '=', location_customer.id)],
                                        order='product_uom_qty desc')
                biggest_order = moves[0].group_id.sale_id.id if moves else False
                biggest_move_qty = moves[0].product_uom_qty if moves else 0
                sales_last_sixty_days = sum(moves.mapped('product_uom_qty'))
                product.write({'biggest_sale_id': biggest_order,
                               'biggest_sale_qty': biggest_move_qty,
                               'last_sixty_days_sales': sales_last_sixty_days})

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

    @api.model
    def compute_rotation_index(self):
        rot_id_a = self.env['ir.config_parameter'].sudo().get_param('rotation.index.a')
        rot_id_b = self.env['ir.config_parameter'].sudo().get_param('rotation.index.b')
        product_values = []
        products = self.env['product.product'].search([('sale_ok', '=', True)])
        rot_a = int(len(products) * (int(rot_id_a)/100))
        rot_b = int(len(products) * (int(rot_id_b)/100))

        for product in products:
            product_values.extend([[product.id, product.last_sixty_days_sales - product.biggest_sale_qty]])
        product_values.sort(key=lambda p: p[1], reverse=True)

        for value in product_values:
            if rot_a > 0:
                products.filtered(lambda p: p.id == value[0]).rotation_index = 1
                rot_a -= 1
            elif rot_b > 0:
                products.filtered(lambda p: p.id == value[0]).rotation_index = 2
                rot_b -= 1
            else:
                products.filtered(lambda p: p.id == value[0]).rotation_index = 3

        product_ko = self.env['product.product'].search([('sale_ok', '=', False)])
        product_ko.write({'rotation_index': 3})


class ProductTemplate(models.Model):

    _inherit = "product.template"

    average_margin = fields.Float("Average Margin Last Sales", readonly=True,
                                  related="product_variant_ids.average_margin")


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
