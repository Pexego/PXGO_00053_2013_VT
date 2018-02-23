# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
from openerp import models, fields, api
import datetime


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    @api.onchange("standard_price")
    @api.depends("standard_price")
    @api.multi
    def _get_pvm(self):
        pricelist = self.env['product.pricelist'].search_read([('name', '=', 'PVM')], ['id'])
        if pricelist:
            pricelist_id = pricelist[0]['id']
            new_ctx = dict(self._context)
            new_ctx.update({
                'pricelist': pricelist_id
            })
            for product in self:
                product_final = self.env['product.template'].with_context(new_ctx).browse(product.id)
                # esto no se si funciona sino habría que volver a instanciar los self.ids
                # con el contexto en un browse o usar api.one pero así nos evitamos que en
                # una entrada múltiple haya que hacer el search_read en tarifas en cada entrada.
                product.pvm_price = product_final.price
                # este campo es calculado y nos devuelve el precio del prodiucto según la tarifa
                # en contexto, acepta también otros parámetros
        else:
            for product in self:
                product.pvm_price = 0.0

    pvm_price = fields.Float("PVM Price", readonly=True, store=True, compute='_get_pvm')


class ProductProduct(models.Model):

    _inherit = 'product.product'

    last_sixty_days_sales = fields.Float('Sales in last 60 days with stock',
                                         readonly=True)
    biggest_sale_qty = fields.Float("Biggest sale qty", readonly=True,
                                    digits=(16, 2))
    biggest_sale_id = fields.Many2one("sale.order", "Biggest order",
                                      readonly=True)
    order_cycle = fields.Integer('Order cycle')
    transport_time = fields.Integer('Transport time')
    security_margin = fields.Integer('Security margin')
    average_margin = fields.Float("Average Margin Last Sales", readonly=True)
    ref_manufacturer = fields.Char(related='manufacturer_pref', readonly=True)

    @api.model
    def compute_last_sixty_days_sales(self, records=False):
        base = datetime.datetime.today()
        sixty_date = (base - datetime.timedelta(days=60)).\
            strftime("%Y-%m-%d %H:%M:%S")
        if not records:
            self.average_margin_last_sales()
            products = self.search([('type', '!=', 'service')])
            product_ids = products.ids
        else:
            product_ids = records
        move_obj = self.env['stock.move']
        sline_obj = self.env['sale.order.line']
        for product_id in product_ids:
            self.env.cr.execute("select min(t.datum) from (select product_id,"
                                "datum from stock_days_positive where "
                                "product_id = %s order by datum desc "
                                "limit 60) as t" % (product_id))
            days_data = self.env.cr.fetchone()
            if days_data:
                product = self.browse(product_id)
                picking_type_obj = self.env['stock.picking.type']
                picking_type_ids = picking_type_obj.search([('code', '=', 'outgoing')])

                moves = move_obj.search([('date', '>=', days_data[0]),
                                         ('state', '=', 'done'),
                                         ('product_id', '=', product.id),
                                         ('picking_type_id', 'in',
                                          picking_type_ids.ids),
                                         ('procurement_id.sale_line_id', '!=',
                                          False)])
                biggest_move_qty = 0.0
                biggest_order = False
                qty = 0.0
                for move in moves:
                    qty += move.product_uom_qty
                    if move.product_uom_qty > biggest_move_qty:
                        biggest_move_qty = move.product_uom_qty
                        biggest_order = \
                            move.procurement_id.sale_line_id.order_id.id



                sale_lines = sline_obj.search([('date_order', '>=',
                                                sixty_date),
                                               ('order_id.state', '=',
                                                'history'),
                                               ('product_id', '=',
                                                product_id)])
                for line in sale_lines:
                    qty += line.product_uom_qty
                    if line.product_uom_qty > biggest_move_qty:
                        biggest_move_qty = line.product_uom_qty
                        biggest_order = \
                            line.order_id.id


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
            sale_order_line_obj = self.env['sale.order.line']
            domain = [('product_id', '=', product_id.id), ('state', 'not in', ('draft', 'cancel', 'exception'))]
            sales_obj = sale_order_line_obj.search(domain, limit=100,
                                                   order='date_order desc')
            margin_perc_sum = 0
            qty_sum = 0
            for line in sales_obj:
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

    @api.one
    @api.depends('order_id', 'order_id.date_order')
    def _get_order_date(self):
        if self.order_id:
            self.date_order = self.order_id.date_order
        else:
            self.date_order = False

    date_order = fields.Date("Date", readonly=True, store=True,
                             compute="_get_order_date")
