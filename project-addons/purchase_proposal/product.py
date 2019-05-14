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


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    @api.multi
    def _get_pvm_price(self, context=None):
        return self.env['product.template'].with_context(context).browse(self.id).price

    @api.onchange("standard_price")
    @api.depends("standard_price")
    @api.multi
    def _get_pvm(self):
        pricelist = self.env['product.pricelist'].search_read([('name', '=', 'PVMA')], ['id', 'name'])
        new_ctx = dict(self._context)
        if pricelist:
            pricelist_id = pricelist[0]['id']
            new_ctx = dict(self._context)
            new_ctx.update({
                'pricelist': pricelist_id
            })
        for product in self:
            price_final = product._get_pvm_price(new_ctx)
            # esto no se si funciona sino habria que volver a instanciar los self.ids
            # con el contexto en un browse o usar api.one pero asi nos evitamos que en
            # una entrada multiple haya que hacer el search_read en tarifas en cada entrada.
            product.pvm_price = price_final
            # este campo es calculado y nos devuelve el precio del producto segun la tarifa
            # en contexto, acepta tambien otros parametros

    @api.onchange("standard_price")
    @api.depends("standard_price")
    @api.multi
    def _get_pvm_b(self):
        pricelist = self.env['product.pricelist'].search_read([('name', '=', 'PVMB')], ['id', 'name'])
        new_ctx = dict(self._context)
        if pricelist:
            pricelist_id = pricelist[0]['id']
            new_ctx = dict(self._context)
            new_ctx.update({
                'pricelist': pricelist_id
            })
        for product in self:
            price_final = product._get_pvm_price(new_ctx)
            product.pvm_price_2 = price_final

    @api.onchange("standard_price")
    @api.depends("standard_price")
    @api.multi
    def _get_pvm_c(self):
        pricelist = self.env['product.pricelist'].search_read([('name', '=', 'PVMC')], ['id', 'name'])
        new_ctx = dict(self._context)
        if pricelist:
            pricelist_id = pricelist[0]['id']
            new_ctx = dict(self._context)
            new_ctx.update({
                'pricelist': pricelist_id
            })
        for product in self:
            price_final = product._get_pvm_price(new_ctx)
            product.pvm_price_3 = price_final

    # Esto en la v11 desaparecera
    pvm_price = fields.Float("PVMA Price", readonly=True, store=True, compute='_get_pvm')
    pvm_price_2 = fields.Float("PVMB Price", readonly=True, store=True, compute='_get_pvm_b')
    pvm_price_3 = fields.Float("PVMB Price", readonly=True, store=True, compute='_get_pvm_c')


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

    @api.one
    @api.depends('order_id', 'order_id.date_order')
    def _get_order_date(self):
        if self.order_id:
            self.date_order = self.order_id.date_order
        else:
            self.date_order = False

    date_order = fields.Date("Date", readonly=True, store=True,
                             compute="_get_order_date")
