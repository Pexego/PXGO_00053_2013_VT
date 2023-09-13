##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
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

from odoo import api, models, fields, _
from odoo.tools.misc import ustr
from odoo.exceptions import except_orm, UserError
import re

PRODUCT_UOM_ID = 1


class PromotionsRulesConditionsExprs(models.Model):
    _inherit = 'promos.rules.conditions.exps'

    attribute = fields.Selection(
        selection_add=[
            ('prod_tag', 'Tag in order'),
            ('order_pricelist', _('Order Pricelist')),
            ('web_discount', 'Web Discount'),
            ('comp_sub_total_brand', 'Compute sub total of brand'),
            ('category_in_order','Product Category in Order'),
            ('order_pricelist_brand', 'Order Pricelist Brand')])

    @api.onchange('attribute')
    def on_change_attribute(self):
        if not self.attribute:
            return
        if self.attribute == 'prod_tag':
            self.value = 'prod_tag'

        if self.attribute == 'order_pricelist':
            self.value = 'pricelist_name'

        if self.attribute == 'web_discount':
            self.value = 'True'

        if self.attribute == 'comp_sub_total_brand':
            self.value = "['product_brand','product_brand2']|0.00"

        if self.attribute == 'category_in_order':
            self.value = "['prod_categ_1','prod_categ_2']"
        if self.attribute == 'order_pricelist_brand':
            self.value = '(pricelist_name_1, pricelist_name_2)'
        return super().on_change_attribute()

    @api.model
    def check_operators(self, operator, attribute):
        operation_list = ['==', '!=', '<=', '<', '>', '>='] if attribute in (
        'web_discount', 'comp_sub_total_brand') else ['in', 'not in']
        if operator not in operation_list:
            raise UserError(f'Only {", ".join(operation_list)} can be used with {attribute}')

    @api.model
    def check_format(self, value, attribute):
        if attribute == 'web_discount' and type(eval(value)) != bool:
            raise UserError(
                "Value for Web discount is invalid\n"
                "Eg for right values: True or False")
        if attribute == 'comp_sub_total_brand':
            if len(value.split("|")) != 2:
                raise UserError(
                    "Value for computed subtotal combination is invalid\n"
                    "Eg for right format is `['brand1,brand2',..]|120.50`")
            product_brands_iter, quantity = value.split("|")
            if not (type(eval(product_brands_iter)) not in [tuple, list] and
                    type(eval(quantity)) in [int, float]):
                raise UserError(
                    "Value for Compute sub total of brand is invalid\n"
                    "Eg for right format is `['brand1,brand2',..]|120.50`")
        if attribute == 'category_in_order' and type(eval(value)) not in [tuple, list]:
            raise UserError(
                "Value for Product Category in Order is invalid\n"
                "Eg for right format is ['prod_categ_1','prod_categ_2',...]")
        if attribute == 'order_pricelist_brand' and type(eval(value)) not in [tuple, list]:
            raise UserError(
                "Value for Order Pricelist Brand in Order is invalid\n"
                "Eg for right format is ['order_pricelist_brand_1','order_pricelist_brand_2',...]")

    def validate(self, vals):
        attribute = vals['attribute']
        comparator = vals['comparator']
        value = vals['value']
        if attribute in ('web_discount','comp_sub_total_brand','category_in_order','order_pricelist_brand'):
            self.check_operators(comparator, attribute)
            self.check_format(value, attribute)
        return super().validate(vals)

    def serialise(self, attribute, comparator, value):
        """
        Constructs an expression from the entered values
        which can be quickly evaluated
        @param attribute: attribute of promo expression
        @param comparator: Comparator used in promo expression.
        @param value: value according which attribute will be compared
        """

        if attribute == 'prod_tag':
            return f'{value} {comparator} prod_tag'
        elif attribute == 'order_pricelist':
            return f'order.pricelist_id.name {comparator} {value}'
        elif attribute == 'web_discount':
            return "web_discount"
        elif attribute == 'comp_sub_total_brand':
            product_brands_iter, quantity = value.split("|")
            return f'sum([brand_sub_total.get(prod_brand,0) for prod_brand in {product_brands_iter}]) {comparator} {quantity}'
        elif attribute == 'category_in_order':
            return f'all([c {comparator} categories for c in {value}])'
        elif attribute == 'order_pricelist_brand':
            list_operator = 'any' if comparator == 'in' else 'all'
            return f'{list_operator}([p {comparator} order_pricelist_brand_ids for p in {value}])'
        else:
            return super().serialise(attribute, comparator, value)

    def evaluate(self, order, **kwargs):
        if self.attribute in ['prod_tag','web_discount','category_in_order','comp_sub_total_brand']:
            prod_tag = []
            web_discount = False
            brand_sub_total = {}
            categories = set()
            for line in order.order_line:
                if line.product_id:
                    if line.product_tags:
                        prod_tag.extend(eval(line.product_tags))
                    if line.web_discount:
                        web_discount = True
                    brand = line.product_id.product_brand_id.name
                    category = line.product_id.categ_id.name
                    categories.add(category)
                    brand_sub_total[brand] = \
                        brand_sub_total.get(brand, 0.00) + \
                        line.price_subtotal
            return eval(self.serialised_expr, locals())
        elif self.attribute == 'order_pricelist_brand':
            order_pricelist_brand_ids = order.pricelist_brand_ids.mapped('name')
            return bool(order_pricelist_brand_ids) and eval(self.serialised_expr, locals())
        return super().evaluate(order,**kwargs)


class PromotionsRulesActions(models.Model):
    _inherit = 'promos.rules.actions'

    action_type = fields.Selection(
        selection_add=[
            ('prod_disc_perc_accumulated',
             _('Discount % on Product accumulated')),
            ('tag_disc_perc',
             _('Discount % on Tag')),
            ('tag_disc_perc_accumulated',
             _('Discount % on Tag accumulated')),
            ('categ_disc_perc',
             _('Discount % on Category')),
            ('categ_disc_perc_accumulated',
             _('Discount % on Categ accumulated')),
            ('brand_disc_perc',
             _('Discount % on Brand')),
            ('brand_disc_perc_accumulated',
             _('Discount % on Brand accumulated')),
            ('brand_price_disc_accumulated',
             _('Discount % on Brand accumulated (Price Unit)')),
            ('web_disc_accumulated',
             _('Web Discount % on Product accumulated')),
            ('a_get_b_product_tag',
             _('AxB on product tag')),
            ('prod_fixed_price_tag',
             _('Fixed price on Product Tag')),
            ('prod_fixed_price',
             _('Fixed price on Product')),
            ('prod_free_per_unit',
             _('Products free per unit')),
            ('sale_points_programme_discount_on_brand',
             _('Sale points programme discount on Brand')),
            ('sale_points_programme_discount_excluding_brands',
             _('Sale points programme discount Excluding Brand')),
            ('disc_per_product',
             _('Discount line per each product')),
            ('fix_price_per_product',
             _('Fixed price per each product')),
            ('tag_disc_perc_line',
             _('New discount line per product with tag')),
            ('change_pricelist_category',
             _('Change pricelist price category')),
            ('change_pricelist_brand',
             _('Change pricelist price brand')),
            ('brand_disc_perc_accumulated_reverse',
             _('Discount % on not Brand accumulated')),
            ('prod_disc_per_qty',
             _('Discount % on one product based on the quantity of another')),
            ('limit_product_units',
             _('Limit quantity of a product in an order')),
            ('cart_disc_perc_exclude_brands',
             _('Discount % on Sub Total excluding brands')),
            ('buy_x_get1free_product_tag',
             _('Buy x and get 1 free group by product tags')),
            ])

    @api.onchange('action_type')
    def on_change(self):
        if self.action_type == 'prod_disc_perc_accumulated':
            self.product_code = 'product_code'
            self.arguments = '0.00'

        elif self.action_type in [
                'tag_disc_perc', 'tag_disc_perc_accumulated']:
            self.product_code = 'tag_name'
            self.arguments = '0.00'

        elif self.action_type in [
                'categ_disc_perc', 'categ_disc_perc_accumulated']:
            self.product_code = 'categ_code'
            self.arguments = '0.00'

        elif self.action_type in [
                'brand_disc_perc', 'brand_disc_perc_accumulated',
                'brand_price_disc_accumulated', 'brand_disc_perc_accumulated_reverse']:
            self.product_code = 'brand_code'
            self.arguments = '0.00'

        elif self.action_type == 'web_disc_accumulated':
            self.arguments = '10.00'

        elif self.action_type == 'a_get_b_product_tag':
            self.product_code = 'product_tag'
            self.arguments = 'A,B'

        elif self.action_type == 'prod_fixed_price_tag':
            self.product_code = 'product_tag'
            self.arguments = '0.00'

        elif self.action_type == 'prod_fixed_price':
            self.product_code = 'product_reference'
            self.arguments = '0.00'

        elif self.action_type == 'prod_free_per_unit':
            self.product_code = '"product_reference",..."'
            self.arguments = '{"product":qty, ...}'

        elif self.action_type in ('sale_points_programme_discount_on_brand', 'sale_points_programme_discount_excluding_brands'):
            self.product_code = '{brand_1: [categ1,categ2],brand_2: []}'
            self.arguments = '[sale_point_rule_name1,sale_point_rule_name2]'

        elif self.action_type == 'disc_per_product':
            self.product_code = '["tag_product","reg_exp_product_code",quantity(optional)]'
            self.arguments = '0.00'

        elif self.action_type == 'prod_disc_per_qty':
            self.product_code = '"product_reference",..."'
            self.arguments = '{"product":discount, ...}'

        elif self.action_type == 'limit_product_units':
            self.product_code = '"product_reference",..."'
            self.arguments = '{"product":qty, ...}'

        elif self.action_type == 'cart_disc_perc_exclude_brands':
            self.product_code = '("brand",...)'
            self.arguments = '0.00'

        return super().on_change()

    def create_line(self, vals):
        if self.env.context.get('end_line', False):
            order = self.env['sale.order'].browse(vals['order_id'])
            vals['sequence'] = 999
            vals['name'] = self.promotion.with_context({'lang': order.partner_id.lang}).line_description
        return super().create_line(vals)

    def action_limit_product_units(self, order):
        product_obj = self.env['product.product']
        products_code = eval(self.product_code)
        products = product_obj.search([('default_code', 'in', products_code)])
        if not products:
            raise UserError(_("No product with the code % s") % products_code)
        products_to_limit_qty = eval(self.arguments)
        for product in products:
            lines = order.order_line.filtered(lambda l: l.product_id == product)
            if not lines:
                continue
            qty = products_to_limit_qty.get(product.default_code)
            total_qty = sum(lines.mapped('product_qty'))
            for line in lines:
                if total_qty <= qty:
                    break
                total_diff = total_qty - qty
                line_diff = line.product_uom_qty - total_diff
                if line_diff >= 0:
                    line.product_uom_qty = line_diff
                    total_qty = 0
                else:
                    total_qty -= line.product_uom_qty
                    line.product_uom_qty = 0

    def action_prod_disc_per_qty(self, order):
        product_obj = self.env['product.product']
        products_code = eval(self.product_code)
        products = product_obj.search([('default_code', 'in', products_code)])
        if not products:
            raise UserError(_("No product with the code % s") % products_code)
        products_to_apply_discount = eval(self.arguments)
        lines = order.order_line.filtered(lambda l: l.product_id in products)
        if lines:
            qty = sum(lines.mapped('product_uom_qty'))
            product_names = products_to_apply_discount.keys()
            lines_to_apply = order.order_line.filtered(lambda l:l.product_id.default_code in product_names)
            for line in lines_to_apply:
                discount = products_to_apply_discount[line.product_id.default_code]
                if line.product_uom_qty<=qty:
                    line.discount=discount
                else:
                    product_qty = line.product_uom_qty
                    line.product_uom_qty = product_qty - qty
                    line.old_qty = product_qty
                    self.create_y_line(order, qty , line.product_id.id)
        return True

    def apply_perc_discount_accumulated(self, order_line):
        final_discount = eval(self.arguments)
        if order_line.discount:
            price_discounted = order_line.price_unit * (
                1 - (order_line.discount or 0.0) / 100.0)
            new_price_unit = price_discounted * \
                (1 - (eval(self.arguments) / 100.0))
            final_discount = 100.0 - (new_price_unit * 100.0 /
                                      order_line.price_unit)
        if order_line.accumulated_promo:
            order_line.write({'discount': final_discount})
        else:
            order_line.write({'discount': final_discount,
                              'old_discount': order_line.discount,
                              'accumulated_promo': True})

    def apply_perc_discount_price_accumulated(self, order_line):
        discount = eval(self.arguments)

        promo_price = order_line.price_unit * (1 - (discount / 100))

        if not order_line.old_price:
            order_line.write({'old_price': order_line.price_unit,
                              'price_unit': promo_price})
        else:
            order_line.write({'price_unit': promo_price})

    def action_tag_disc_perc_accumulated(self, order):
        """
        Action for 'Discount % on Product'
        @param cursor: Database Cursor
        @param user: ID of User
        @param action: Action to be taken on sale order
        @param order: sale order
        @param context: Context(no direct use).
        """
        for order_line in order.order_line:
            if eval(self.product_code) in eval(order_line.product_tags):
                self.apply_perc_discount_accumulated(order_line)
        return {}

    def action_categ_disc_perc_accumulated(self, order):
        for order_line in order.order_line:
            if eval(self.product_code) in order_line.product_id.categ_id.display_name:
                self.apply_perc_discount_accumulated(order_line)
        return {}

    def action_brand_disc_perc_accumulated(self, order):
        for order_line in order.order_line:
            if eval(self.product_code) == \
                    order_line.product_id.product_brand_id.code:
                self.apply_perc_discount_accumulated(order_line)
        return {}

    def action_prod_disc_perc_accumulated(self, order):
        for order_line in order.order_line:
            if order_line.product_id.code == eval(self.product_code):
                self.apply_perc_discount_accumulated(order_line)

    def apply_perc_discount(self, order_line):
        vals = {
            'discount': eval(self.arguments),
            'old_discount': order_line.discount
        }
        return order_line.write(vals)

    def action_tag_disc_perc(self, order):
        """
        Action for 'Discount % on Product'
        @param cursor: Database Cursor
        @param user: ID of User
        @param action: Action to be taken on sale order
        @param order: sale order
        @param context: Context(no direct use).
        """
        for order_line in order.order_line:
            if eval(self.product_code) in eval(order_line.product_tags):
                self.apply_perc_discount(order_line)
        return {}

    def action_categ_disc_perc(self, order):
        for order_line in order.order_line:
            if eval(self.product_code) in order_line.product_id.categ_id.display_name:
                self.apply_perc_discount(order_line)
        return {}

    def action_brand_disc_perc(self, order):
        for order_line in order.order_line:
            if eval(self.product_code) == \
                    order_line.product_id.product_brand_id.code:
                self.apply_perc_discount(order_line)
        return {}

    def action_web_disc_accumulated(self, order):
        for order_line in order.order_line:
            if order_line.web_discount:
                self.apply_perc_discount_accumulated(order_line)
        return {}

    def action_a_get_b_product_tag(self, order):
        promo_products = []
        qty_a, qty_b = [eval(arg) for arg in self.arguments.split(",")]
        for order_line in order.order_line.filtered(
                lambda l: not l.promotion_line):
            if order_line.product_id.id not in promo_products:
                if eval(self.product_code) in order_line.product_id.tag_ids.mapped('name'):
                    qty = 0
                    for order_line_2 in order.order_line:
                        if order_line_2.product_id.id == order_line.product_id.id:
                            qty += order_line_2.product_uom_qty
                    num_lines = int(qty / qty_a) * (qty_a - qty_b)
                    if qty - qty_a >= 0:
                        self.create_y_line_axb(
                            order, order_line,num_lines)
                        promo_products.append(order_line.product_id.id)
        return {}

    def action_buy_x_get1free_product_tag(self, order):
        """
        Generates one line of discount for each group of products
        Given the size of the group and the tag of the products
        Gets first the less expensive
        """
        qty = eval(self.arguments)

        promo_products = order.order_line.filtered(lambda l: not l.promotion_line and eval(self.product_code) in l.product_id.tag_ids.mapped('name'))
        promo_products_sorted = promo_products.sorted('price_unit')
        expanded_products = []
        # Sets in a list, as much ids as qty there is.
        # order.line(id1, id2) -> [id1, id1, id1, id2, id2]
        # That means order.line(id1) has product_uom_qty = 3 and That means order.line(id2) has product_uom_qty = 2
        for prod in promo_products_sorted:
            expanded_products += [prod.id]*int(prod.product_uom_qty)
        for line in range(int(sum(promo_products.mapped('product_uom_qty'))/qty)):
            self.create_y_line_axb(order, promo_products.filtered(lambda p: p.id == expanded_products[line]), 1)
        return {}

    def action_prod_fixed_price_tag(self, order):
        for order_line in order.order_line:
            if eval(self.product_code) in eval(order_line.product_tags):
                self.apply_fixed_price(order_line)
        return {}

    def action_prod_fixed_price(self, order):
        for order_line in order.order_line:
            if order_line.product_id.default_code in eval(self.product_code):
                self.apply_fixed_price(order_line)
        return {}

    def apply_fixed_price(self, order_line):
        vals = {
            'price_unit': eval(self.arguments)
        }
        return order_line.write(vals)

    def create_y_line_axb(self, order, order_line, quantity):
        product_id = order_line.product_id
        vals = {
            'order_id': order.id,
            'sequence': order_line.sequence,
            'product_id': self.env.ref('commercial_rules.product_discount').id,
            'name': f"{product_id.default_code} ({self.promotion.with_context({'lang': order.partner_id.lang}).line_description})",
            'price_unit': -order_line.price_unit,
            'discount': order_line.discount,
            'promotion_line': True,
            'product_uom_qty': quantity,
            'product_uom': product_id.uom_id.id,
            'original_line_id_promo': order_line.id,
            'promo_qty_split': eval(self.arguments.split(",")[0])

        }
        self.create_line(vals)
        return True

    def action_prod_free_per_unit(self, order):
        """
        Action for: Get Product for free per unit
        """
        product_obj = self.env['product.product']
        # Get Product
        products_code = eval(self.product_code)
        products = product_obj.search([('default_code', 'in', products_code)])
        if not products:
            raise UserError(_("No product with the code % s") % products_code)
        for line in order.order_line.filtered(lambda l: l.product_id in products):
            promo_products = eval(self.arguments)
            for product, qty in promo_products.items():
                prod = product_obj.search([('default_code', '=', product)])
                self.create_y_line(order, qty * line.product_qty, prod.id)

        return True

    def create_y_line_sale_points_programme(self, order, price_unit,bags_ids):
        product_id = self.env.ref('commercial_rules.product_discount')
        vals = {
            'order_id': order.id,
            'product_id': product_id.id,
            'name': '%s' % self.promotion.with_context({'lang': order.partner_id.lang}).line_description,
            'price_unit': -price_unit,
            'promotion_line': True,
            'product_uom_qty': 1,
            'product_uom': product_id.uom_id.id,
            'bag_ids': [(6, 0, bags_ids.ids)]
        }
        self.create_line(vals)
        return True

    def apply_bags(self, order, points, bags):
        """
            Creates a discount line, finished the bags and recalculate partner points accumulated
        :param order: sale.order
        :param points: point to discount
        :param bags: bags to apply
        """
        self.create_y_line_sale_points_programme(order, points, bags)
        bags.write({'applied_state': 'applied', 'order_applied_id': order.id})
        self.env['res.partner.point.programme.bag'].sudo().\
            with_delay(priority=11, eta=10).recalculate_partner_point_bag_accumulated(bags.mapped('point_rule_id'), order.partner_id)

    def _get_max_bags_to_apply_points(self, bags, price_subtotal):
        """
            Get the maximum bags to apply dor this price_subtotal
        :param bags:
        :param price_subtotal:
        :return:
        """
        bags_to_change_status = self.env['res.partner.point.programme.bag']
        bag_obj = self.env['res.partner.point.programme.bag']
        cont_point_applied = 0
        for bag in bags:
            rule = bag.point_rule_id
            if price_subtotal <= cont_point_applied:
                break
            bag_points = bag.points
            if cont_point_applied + bag_points <= price_subtotal:
                cont_point_applied += bag_points
                bags_to_change_status += bag
            else:
                diff = price_subtotal - cont_point_applied
                old_points = bag.points
                bag.points = diff
                bag_obj.create({'name': rule.name,
                                'point_rule_id': rule.id,
                                'order_id': bag.order_id.id,
                                'points': old_points - diff,
                                'partner_id': bag.partner_id.id})
                cont_point_applied = price_subtotal
                bags_to_change_status += bag
        return bags_to_change_status

    def _apply_max_points(self, order, price_subtotal):
        """ Apply max points given an order and a price_subtotal of the rules in self.arguments
        :param order: sale.order
        :param price_subtotal: max points to apply
        :return: True if points are equals or less than 0
        """
        bag_obj = self.env['res.partner.point.programme.bag']
        rule_obj = self.env['sale.point.programme.rule']
        rules = rule_obj.search([('name', 'in', eval(self.arguments))])
        bags = bag_obj.search([('partner_id', '=', order.partner_id.id), ('point_rule_id', 'in', rules.ids),
                               ('applied_state', '=', 'no')])
        points = sum(bags.mapped('points'))
        if points <= 0:
            return True
        if points <= price_subtotal:
            self.apply_bags(order, points, bags)
        else:
            bags_to_change_status = self._get_max_bags_to_apply_points(bags, price_subtotal)
            self.apply_bags(order, price_subtotal, bags_to_change_status)

    def _get_subtotal_to_apply_points(self, order, mode):
        """
        variables:
        ------------
        self.product_code: dict[str, list[str]]  i.e.  {'brand_1':['categ_1','categ_2'], 'brand_2':['categ_3','categ_4']}
            if mode = 'exclude'  if the values for a certain key are empty ([]) it means that it exclude all categories for this brand
            if mode = 'include' if the values for a certain key are empty ([]) it means that it applies to all categories for this brand
        :param order: sale.order
        :param mode: it can be 'include' or 'exclude'.
        :return: sum of the subtotal prices of the order lines of the order that applies the condition of excluding/including brands
        """
        price_subtotal = 0
        brand_category_dict = eval(self.product_code)
        for line in order.order_line:
            product_brand = line.product_id.product_brand_id.code
            if not product_brand:
                continue
            categs = brand_category_dict.get(product_brand, False)
            if ((mode == 'include' and product_brand not in brand_category_dict) or (
                mode == 'exclude' and product_brand in brand_category_dict)) and not categs:
                continue
            eval_categ = not categs
            if categs:
                categ_display_name = line.product_id.categ_id.display_name
                if mode == 'include':
                    eval_categ = any([c in categ_display_name for c in categs])
                else:
                    eval_categ = all([c not in categ_display_name for c in categs])
            if eval_categ:
                price_subtotal += line.price_subtotal
        return price_subtotal

    def _apply_sale_points_programme(self, order, mode):
        """
            Apply sale points programme to an order excluding/including brand
        :param order: sale.order to apply points
        :param mode: it can be 'include' or 'exclude'.
        :return: True when finish
        """
        price_subtotal = self._get_subtotal_to_apply_points(order, mode)
        if price_subtotal <= 0:
            return True
        self._apply_max_points(order, price_subtotal)
        return True

    def action_sale_points_programme_discount_on_brand(self, order):
        """
        Action for: Sale points programme discount on a selected brand
        """
        return self._apply_sale_points_programme(order, 'include')

    def action_sale_points_programme_discount_excluding_brands(self, order):
        """
        Action for: Sale points programme discount excluding brands
        """
        return self._apply_sale_points_programme(order, 'exclude')

    def action_brand_price_disc_accumulated(self, order):
        for order_line in order.order_line:
            if eval(self.product_code) == \
                    order_line.product_id.product_brand_id.code:
                self.apply_perc_discount_price_accumulated(order_line)
        return {}

    @staticmethod
    def get_qty_by_tag(tag, order):
        if not tag or not order:
            return 0
        return sum(order.order_line
                   .filtered(lambda l, promo_tag=tag: promo_tag in l.product_id.tag_ids._get_tag_recursivity())
                   .mapped('product_uom_qty'))

    @staticmethod
    def get_new_lines(products_exp, products_tag):
        new_lines = []
        for count, product in enumerate(products_exp):
            if count >= products_tag :
                break
            else:
                # Group by products with same price
                if count > 0 and product[1] == products_exp[count - 1][1]:
                    new_lines[len(new_lines) - 1][0] += 1
                else:
                    new_lines.append([1, product[0], product[1]])
        return new_lines

    @staticmethod
    def get_match_products(order, condition_exp):
        products_exp = []
        for line in order.order_line:
            if eval(condition_exp):
                for _ in range(int(line.product_uom_qty)):
                    price_unit = round(line.price_subtotal / line.product_uom_qty, 2)
                    products_exp.append([price_unit, line.product_id.default_code])
        products_exp.sort()
        return products_exp

    def create_lines_per_product(self, order, new_lines, price_unit_exp):
        for line in new_lines:
            vals = {
                'sequence': 999,
                'order_id': order.id,
                'product_id': self.env.ref('commercial_rules.product_discount').id,
                'name': 'Promo %s - %s' % (
                    self.promotion.with_context({'lang': order.partner_id.lang}).line_description, line[2]),
                'price_unit': eval(price_unit_exp),
                'discount': 0.0,
                'promotion_line': True,
                'product_uom_qty': line[0],
                'product_uom': 1
            }
            self.create_line(vals)

    def action_disc_per_product(self, order):
        product_code = eval(self.product_code)
        # first get all the product with the tag
        products_tag = self.get_qty_by_tag(product_code[0], order)
        # ["tag_product","reg_exp_product_code", Optionally a third parameter that indicates the maximum amount to which
        # it applies per product. Default is 1]
        if len(product_code) > 2:
            products_tag *= product_code[2]
        # then, get a dict with all the products that match the condition
        products_exp = []
        if products_tag > 0:
            products_exp = self.get_match_products(order,
                                                   condition_exp="re.match('%s', line.product_id.default_code)" % product_code[1])

        new_lines = self.get_new_lines(products_exp, products_tag)
        # new_lines -> [[qty, price, product], [qty, price, product], ...]

        # Finally, create all new_lines with discount 0% and expression price evaluated as price
        self.create_lines_per_product(order, new_lines,
                                      price_unit_exp="-line[1] * ((%s or 0.0) / 100.0)" % eval(self.arguments))

    def action_fix_price_per_product(self, order):
        # first get all the product with the tag
        products_tag = self.get_qty_by_tag(eval(self.product_code), order)
        # then, get a dict with all the products that match the condition
        products_exp = []
        if products_tag > 0:
            products_exp = self.get_match_products(order,
                                                  condition_exp="line.product_id.default_code in %s" % list(eval(self.arguments).keys()))

        new_lines = self.get_new_lines(products_exp, products_tag)
        # new_lines -> [[qty, price, product], [qty, price, product], ...]
        # Finally, create all new_lines with discount 0% and expression price evaluated as price
        self.create_lines_per_product(order, new_lines,
                                      price_unit_exp="-(line[1] - %s[line[2]])" % eval(self.arguments))

    def action_tag_disc_perc_line(self, order):
        for order_line in order.order_line:
            if eval(self.product_code) in eval(order_line.product_tags):
                vals = {
                    'sequence': 999,
                    'order_id': order.id,
                    'product_id': self.env.ref('commercial_rules.product_discount').id,
                    'name': 'Promo %s' % order_line.product_id.default_code,
                    'price_unit': -(order_line.price_subtotal * (int(self.arguments)/100)),
                    'discount': 0.0,
                    'promotion_line': True,
                    'product_uom_qty': 1,
                    'product_uom': 1
                }
                self.create_line(vals)
        return {}

    def action_change_pricelist_category(self, order):
        for order_line in order.order_line:
            if eval(self.product_code) in order_line.product_id.categ_id.display_name:
                self.change_pricelist_line(order_line)
        return {}

    def action_change_pricelist_brand(self, order):
        for order_line in order.order_line:
            if eval(self.product_code) == \
                    order_line.product_id.product_brand_id.name:
                self.change_pricelist_line(order_line)
        return {}

    def change_pricelist_line(self, order_line):
        new_pricelist_argument = eval(self.arguments)
        product = order_line.product_id
        new_pricelist = self.env['product.pricelist'].search([('name', '=', new_pricelist_argument)])
        price_unit = self.env['account.tax']._fix_tax_included_price_company(
            self._get_display_price_from_pricelist(product, new_pricelist, order_line),
            product.taxes_id, order_line.tax_id, order_line.company_id)
        order_line.write({'price_unit': price_unit, 'discount': 0.0, 'old_discount': 0.0, 'accumulated_promo': False})

    @api.multi
    def _get_display_price_from_pricelist(self, product, pricelist, order_line):
        # This is a copy of _get_display_price, but here we specify the pricelist
        if pricelist.discount_policy == 'with_discount':
            return product.with_context(pricelist=pricelist.id).price
        product_context = dict(self.env.context, partner_id=order_line.order_id.partner_id.id, date=order_line.order_id.date_order,
                               uom=order_line.product_uom.id)
        final_price, rule_id = pricelist.with_context(product_context).get_product_price_rule(
            product, order_line.product_uom_qty or 1.0, order_line.order_id.partner_id)
        base_price, currency_id = order_line.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                              order_line.product_uom_qty,
                                                                                              order_line.product_uom,
                                                                                              pricelist.id)
        if currency_id != pricelist.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(product_context).compute(base_price,
                                                                                                            pricelist.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    def action_brand_disc_perc_accumulated_reverse(self, order):
        for order_line in order.order_line:
            if eval(self.product_code) != \
                    order_line.product_id.product_brand_id.code and order_line.product_id.type == 'product':
                self.apply_perc_discount_accumulated(order_line)
        return {}

    def action_cart_disc_perc(self, order):
        return super(PromotionsRulesActions, self.with_context({'end_line': True})).action_cart_disc_perc(order)

    def action_cart_disc_perc_exclude_brands(self, order):
        """
        Discount % on Sub Total excluding brands
        """
        amt_untaxed_filtered = sum([line.price_subtotal for line in order.order_line.filtered(
            lambda l: l.product_id.product_brand_id.name not in eval(self.product_code)
        )])

        args = {
            'order_id': order.id,
            'name': self.promotion.name,
            'price_unit': -(amt_untaxed_filtered * eval(self.arguments) / 100),
            'product_uom_qty': 1,
            'promotion_line': True,
            'product_uom': PRODUCT_UOM_ID,
            'product_id': self.env.ref('commercial_rules.product_discount').id
        }
        self.with_context({'end_line': True}).create_line(args)
        return True


class PromotionsRules(models.Model):

    _inherit = "promos.rules"

    special_promo = fields.Boolean("Special Promo")

    line_description = fields.Char(translate=True, string="Desciption in lines",
                                   help="This field is shown in the description field of the invoice,picking and sale lines")

    apply_at_confirm = fields.Boolean("Apply at confirm")

    partner_categories_excluded = fields.Many2many('res.partner.category',
                                                   'rule_partner_cat_rel_ex',
                                                   'category_id',
                                                   'rule_id',
                                                   copy=True,
                                                   string="Partner Categories Excluded")

    @api.model
    def apply_special_promotions(self, order):
        domain = self._get_promotions_domain(order)
        domain += [('special_promo', '=', True)]
        active_promos = self.search(domain)

        for promotion_rule in active_promos:
            result = promotion_rule.evaluate(order)
            #If evaluates to true
            if result:
                try:
                    promotion_rule.execute_actions(order)
                except Exception as e:
                    raise except_orm("Promotions", ustr(e))
                #If stop further is true
                if promotion_rule.stop_further:
                    return True
        return True

    @api.model
    def _get_promotions_domain(self, order):
        domain = super()._get_promotions_domain(order)
        if order.partner_id.category_id:
            categ_ids = [x.id for x in order.partner_id.category_id]
            domain += ['|', ('partner_categories_excluded', 'not in', categ_ids),
                       ('partner_categories_excluded', '=', False)]
        if self.env.context.get('is_confirm', False):
            return domain
        else:
            domain += [('apply_at_confirm', '=', False)]
            return domain
