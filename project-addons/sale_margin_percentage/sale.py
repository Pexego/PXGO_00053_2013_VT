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

        if self.product_id and self.product_id.standard_price:
            self.purchase_price = self.product_id.standard_price
            margin = round((self.price_unit * self.product_uom_qty *
                            (100.0 - self.discount) / 100.0) -
                           (self.purchase_price * self.product_uom_qty), 2)
            self.margin_perc = round((margin * 100) /
                                     ((self.purchase_price *
                                       self.product_uom_qty)
                                      or 1.0), 2)
            self.margin = margin

    margin = fields.Float(compute="_product_margin", string='Margin',
                          store=True, multi='marg', readonly=True)
    margin_perc = fields.Float(compute="_product_margin", string='Margin %',
                               store=True, multi='marg', readonly=True)
    purchase_price = fields.Float(compute="_product_margin", readonly=True,
                                  string="Purchase price", store=True,
                                  multi='marg')


class sale_order(models.Model):

    _inherit = "sale.order"

    @api.one
    @api.depends("order_line.margin", "order_line.deposit")
    def _product_margin(self):
        total_purchase = self.total_purchase

        self.margin = 0.0
        margin = 0.0
        if total_purchase != 0:
            for line in self.order_line:
                if not line.deposit:
                    margin += line.margin or 0.0
            self.margin = round((margin * 100) / total_purchase, 2)

    @api.one
    def _get_total_price_purchase(self):
        self.total_purchase = 0.0
        for line in self.order_line:
            # ADDED for dependency with stock_deposit for not count
            # deposit in total margin
            if not line.deposit:
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
