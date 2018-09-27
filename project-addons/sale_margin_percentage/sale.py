# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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


class sale_order_line(models.Model):

    _inherit = "sale.order.line"

    @api.one
    @api.depends("product_uom_qty", "price_unit", "discount", "product_id")
    def _product_margin(self):
        self.margin = 0.0
        self.margin_perc = 0.0
        self.purchase_price = 0.0

        if self.product_id and self.product_id.standard_price and \
                not self.pack_depth:
            self.purchase_price = self.product_id.standard_price
            sale_price = self.price_unit * self.product_uom_qty * \
                ((100.0 - self.discount) / 100.0)
            purchase_price = self.purchase_price * self.product_uom_qty
            margin = round(sale_price - purchase_price, 2)
            if sale_price:
                if sale_price < purchase_price:
                    self.margin_perc = round((margin * 100) / purchase_price, 2)
                else:
                    self.margin_perc = round((margin * 100) / sale_price, 2)
            elif sale_price == 0.0 and self.discount == 100:
                self.margin_perc = -100
            self.margin = margin

    @api.one
    @api.depends("product_uom_qty", "price_unit", "discount", "product_id")
    def _product_margin_rappel(self):
        self.margin_perc_rappel = 0.0
        self.purchase_price = 0.0

        if self.product_id and self.product_id.standard_price and not self.pack_depth:

            self.purchase_price = self.product_id.standard_price

            sale_price = self.price_unit * self.product_uom_qty * ((100.0 - self.discount) / 100.0)
            purchase_price = self.purchase_price * self.product_uom_qty
            if self.product_id.product_brand_id.name in self.env['rappel'].search([('name', 'like', 'Vale Ahorro%')],limit=1).mapped('brand_ids.name'):
                if self.order_id.partner_id.property_product_pricelist.name in ('PVPA 55', 'PVPB 55', 'PVPC 55'):
                    rappel = sale_price * 0.10
                elif self.order_id.partner_id.property_product_pricelist.name in ('PVPA 52,5', 'PVPB 52,5', 'PVPC 52,5'):
                    rappel = sale_price * 0.05
                else:
                    rappel = 0.0
            else:
                rappel = 0.0
            sale_price_rappel = sale_price - rappel
            margin = round(sale_price_rappel - purchase_price, 2)

            if sale_price:
                if sale_price < purchase_price:
                    self.margin_perc_rappel = round((margin * 100) / purchase_price, 2)
                else:
                    self.margin_perc_rappel = round((margin * 100) / sale_price_rappel, 2)
            elif sale_price == 0.0 and self.discount == 100:
                self.margin_perc_rappel = -100
            self.margin_rappel = margin

    margin = fields.Float(compute="_product_margin", string='Margin',
                          store=True, multi='marg', readonly=True)
    margin_rappel = fields.Float(compute="_product_margin_rappel", string='Margin with rappel',
                          store=True, multi='marg', readonly=True)
    margin_perc = fields.Float(compute="_product_margin", string='Margin %',
                               store=True, multi='marg', readonly=True)
    purchase_price = fields.Float(compute="_product_margin", readonly=True,
                                  string="Purchase price", store=True,
                                  multi='marg')
    margin_perc_rappel = fields.Float(compute="_product_margin_rappel", string='Margin',
                               store=True, multi='marg', readonly=True, help='Margin after the Coupon rappel')


class sale_order(models.Model):

    _inherit = "sale.order"

    @api.multi
    def fix_sale_margin(self):
        """Funcion para recalcular margenes incorrectos"""
        for sale in self:
            sale.order_line._product_margin()
            sale._product_margin()


    @api.one
    @api.depends("order_line.margin", "order_line.deposit")
    def _product_margin(self):
        self.margin = 0.0
        margin = 0.0
        sale_price = 0.0
        for line in self.order_line:
            if not line.deposit and not line.pack_depth:
                if line.price_unit > 0:
                    margin += line.margin or 0.0
                else:
                    margin += line.price_unit
                sale_price += line.price_subtotal or 0.0
        if sale_price:
            self.margin = round((margin * 100) / sale_price, 2)

    @api.one
    @api.depends("order_line.margin_rappel", "order_line.deposit")
    def _product_margin_rappel(self):
        self.margin_rappel = 0.0
        margin_rappel = 0.0
        sale_price = 0.0
        for line in self.order_line:
            if not line.deposit and not line.pack_depth:
                if line.price_unit > 0:
                    margin_rappel += line.margin_rappel or 0.0
                else:
                    margin_rappel += line.price_unit
                sale_price += line.price_subtotal or 0.0
        if sale_price:
            self.margin_rappel = round((margin_rappel * 100) / sale_price, 2)

    @api.one
    def _get_total_price_purchase(self):
        self.total_purchase = 0.0
        for line in self.order_line:
            # ADDED for dependency with stock_deposit for not count
            # deposit in total margin
            if not line.deposit and not line.pack_depth:
                if line.purchase_price:
                    self.total_purchase += line.purchase_price * \
                        line.product_uom_qty
                elif line.product_id:
                    cost_price = line.product_id.standard_price
                    self.total_purchase += cost_price * \
                        line.product_uom_qty

    total_purchase = fields.Float(compute="_get_total_price_purchase",
                                  string='Price purchase', readonly=True)
    margin = fields.Float(compute="_product_margin", string='Margin',
                          help="It gives profitability by calculating "
                               "percentage.", store=True, readonly=True)
    margin_rappel = fields.Float(compute="_product_margin_rappel", string='Margin',
                          help="Margin based on the coupon rappel", store=True, readonly=True)
