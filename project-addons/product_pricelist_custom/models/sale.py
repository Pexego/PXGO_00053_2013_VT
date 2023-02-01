from odoo import models,api

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        """ This method extend _onchange_discount to calculate the discount of a product which has special pricelist
            instead of normal partner pricelist
            :return: discount of a pricelist product
        """
        pricelists = self.order_id.partner_id.pricelist_brand_ids.filtered(
            lambda p: self.product_id.product_brand_id in p.brand_group_id.brand_ids)
        if not pricelists:
            return super()._onchange_discount()
        if not (self.product_id and self.product_uom and
                        self.order_id.partner_id and pricelists and
                        pricelists.discount_policy == 'without_discount' and
                        self.env.user.has_group('sale.group_discount_per_so_line')):
                    return
        self.discount = 0.0
        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=pricelists,
            uom=self.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order,
                               uom=self.product_uom.id)

        price, rule_id = pricelists.with_context(product_context).get_product_price_rule(
            self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        new_list_price, currency_id = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                                  self.product_uom_qty,
                                                                                                  self.product_uom,
                                                                                                  pricelists.id)

        if new_list_price != 0:
            if pricelists.currency_id.id != currency_id:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = self.env['res.currency'].browse(currency_id).with_context(product_context).compute(
                    new_list_price, pricelists.currency_id)
            discount = (new_list_price - price) / new_list_price * 100
            if discount > 0:
                self.discount = discount

    @api.multi
    def _get_display_price(self, product):
        """ This method extend _get_display_price to calculate the price of a product which has special pricelist
            instead of normal partner pricelist
            :param product: product.product
            :return: price of a pricelist product
        """
        pricelists = self.order_id.partner_id.pricelist_brand_ids.filtered(lambda p:product.product_brand_id in p.brand_group_id.brand_ids)
        if pricelists:
            product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order,
                                   uom=self.product_uom.id)
            final_price, rule_id = pricelists.with_context(product_context).get_product_price_rule(
                self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
            if pricelists.discount_policy == 'without_discount':
                base_price, currency_id = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                                      self.product_uom_qty,
                                                                                                      self.product_uom,
                                                                                                      pricelists.id)
                if currency_id != self.order_id.pricelist_id.currency_id.id:
                    base_price = self.env['res.currency'].browse(currency_id).with_context(product_context).compute(base_price,
                                                                                                                    pricelists.currency_id)
                return max(final_price, base_price)
            return final_price
        return super()._get_display_price(product)
