# -*- coding: utf-8 -*-
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

try:
    #Backward compatible
    from sets import Set as set
except:
    pass

from openerp.osv import osv, orm, fields
from openerp.tools.misc import ustr
from openerp import netsvc
from openerp.tools.translate import _

# LOGGER = netsvc.Logger()
DEBUG = False
PRODUCT_UOM_ID = 1
ATTRIBUTES = [
    ('amount_untaxed', _('Untaxed Total')),
    ('amount_tax', 'Tax Amount'),
    ('amount_total', 'Total Amount'),
    ('prod_tag', 'Tag in order'),
    ('product', 'Product Code in order'),
    ('prod_qty', 'Product Quantity combination'),
    ('prod_unit_price', 'Product UnitPrice combination'),
    ('prod_sub_total', 'Product SubTotal combination'),
    ('prod_discount', 'Product Discount combination'),
    ('prod_weight', 'Product Weight combination'),
    ('comp_sub_total', 'Compute sub total of products'),
    ('comp_sub_total_x', 'Compute sub total excluding products'),
    ('custom', 'Custom domain expression'),
    ('order_pricelist', _('Order Pricelist')),
    ('web_discount', 'Web Discount')
]

ACTION_TYPES = [
    ('prod_disc_perc', _('Discount % on Product')),
    ('prod_disc_perc_accumulated', _('Discount % on Product accumulated')),
    ('tag_disc_perc', _('Discount % on Tag')),
    ('tag_disc_perc_accumulated', _('Discount % on Tag accumulated')),
    ('categ_disc_perc', _('Discount % on Category')),
    ('categ_disc_perc_accumulated', _('Discount % on Categ accumulated')),
    ('brand_disc_perc', _('Discount % on Brand')),
    ('brand_disc_perc_accumulated', _('Discount % on Brand accumulated')),
    ('prod_disc_fix', _('Fixed amount on Product')),
    ('cart_disc_perc', _('Discount % on Sub Total')),
    ('cart_disc_fix', _('Fixed amount on Sub Total')),
    ('prod_x_get_y', _('Buy X get Y free')),
    ('web_disc_accumulated', _('Web Discount % on Product accumulated'))
]


class PromotionsRulesConditionsExprs(orm.Model):
    _inherit = 'promos.rules.conditions.exps'

    def on_change(self, cursor, user, ids=None,
                  attribute=None, value=None, context=None):
        """
        Set the value field to the format if nothing is there
        @param cursor: Database Cursor
        @param user: ID of User
        @param ids: ID of current record.
        @param attribute: attribute sent by caller.
        @param value: Value sent by caller.
        @param context: Context(no direct use).
        """
        # If attribute is not there then return.
        # Will this case be there?
        if not attribute:
            return {}
        # If value is not null or one of the defaults
        if value not in [False,
                         "'product_code'",
                         "'product_code',0.00",
                         "['product_code','product_code2']|0.00",
                         "0.00",
                         ]:
            return {}
        # Case 1
        if attribute == 'product':
            return {
                    'value':{
                             'value':"'product_code'"
                             }
                    }
        if attribute == 'prod_tag':
            return {'value': {'value':"'prod_tag'"}}

         #Case 2
        if attribute in [
                         'prod_qty',
                         'prod_unit_price',
                         'prod_sub_total',
                         'prod_discount',
                         'prod_weight',
                         'prod_net_price',
                         ]:
            return {
                    'value':{
                             'value':"'product_code',0.00"
                             }
                    }
        # Case 3
        if attribute in [
                         'comp_sub_total',
                         'comp_sub_total_x',
                         ]:
            return {
                    'value':{
                             'value':"['product_code','product_code2']|0.00"
                             }
                    }
        # Case 4
        if attribute in ['amount_untaxed',
                         'amount_tax',
                         'amount_total']:
            return {
                'value': {
                    'value': "0.00"
                }
            }
        if attribute in ['order_pricelist']:
            return {
                'value': {
                    'value': "'pricelist_name'"
                }
            }

        if attribute == 'web_discount':
            return {
                'value': {
                    'value': "True"
                }
            }

        return {}
    _columns = {
        'attribute': fields.selection(ATTRIBUTES,
                                      'Attribute',
                                      size=50,
                                      required=True)
    }

    def validate(self, cursor, user, vals, context=None):
        """
        Checks the validity
        @param cursor: Database Cursor
        @param user: ID of User
        @param vals: Values of current record.
        @param context: Context(no direct use).
        """
        NUMERCIAL_COMPARATORS = ['==', '!=', '<=', '<', '>', '>=']
        ITERATOR_COMPARATORS = ['in', 'not in']
        attribute = vals['attribute']
        comparator = vals['comparator']
        value = vals['value']
        #Mismatch 1:
        if attribute in [
                         'amount_untaxed',
                         'amount_tax',
                         'amount_total',
                         'prod_qty',
                         'prod_unit_price',
                         'prod_sub_total',
                         'prod_discount',
                         'prod_weight',
                         'prod_net_price',
                         'comp_sub_total',
                         'comp_sub_total_x',
                         'web_discount',
                         ] and \
            not comparator in NUMERCIAL_COMPARATORS:
            raise Exception(
                            "Only %s can be used with %s"
                            % ",".join(NUMERCIAL_COMPARATORS), attribute
                            )
        #Mismatch 2:
        if (attribute == 'product'  or attribute == 'prod_tag') and \
            not comparator in ITERATOR_COMPARATORS:
            raise Exception(
                            "Only %s can be used with Product Code or Tags"
                            % ",".join(ITERATOR_COMPARATORS)
                            )
        #Mismatch 3:
        if attribute in [
                         'prod_qty',
                         'prod_unit_price',
                         'prod_sub_total',
                         'prod_discount',
                         'prod_weight',
                         'prod_net_price',
                         ]:
            try:
                product_code, quantity = value.split(",")
                if not (type(eval(product_code)) == str \
                    and type(eval(quantity)) in [int, long, float]):
                    raise
            except:
                raise Exception(
                        "Value for %s combination is invalid\n"
                        "Eg for right format is `'PC312',120.50`" % attribute)
        #Mismatch 4:
        if attribute in [
                         'comp_sub_total',
                         'comp_sub_total_x',
                         ]:
            try:
                product_codes_iter, quantity = value.split("|")
                if not (type(eval(product_codes_iter)) in [tuple, list] \
                    and type(eval(quantity)) in [int, long, float]):
                    raise
            except:
                raise Exception(
                        "Value for computed subtotal combination is invalid\n"
                        "Eg for right format is `['code1,code2',..]|120.50`")
        # After all validations say True
        return True

    def serialise(self, attribute, comparator, value):
        """
        Constructs an expression from the entered values
        which can be quickly evaluated
        @param attribute: attribute of promo expression
        @param comparator: Comparator used in promo expression.
        @param value: value according which attribute will be compared
        """
        if attribute == 'custom':
            return value
        if attribute == 'product':
            return '%s %s products' % (value,
                                       comparator)
        if attribute == 'prod_tag':
            return '%s %s prod_tag' % (value, comparator)
        if attribute == 'order_pricelist':
            return """order.pricelist_id.name %s %s""" % (comparator, value)
        if attribute in [
                         'prod_qty',
                         'prod_unit_price',
                         'prod_sub_total',
                         'prod_discount',
                         'prod_weight',
                         'prod_net_price',
                         ]:
            product_code, quantity = value.split(",")
            return '(%s in products) and (%s["%s"] %s %s)' % (
                                                           product_code,
                                                           attribute,
                                                           eval(product_code),
                                                           comparator,
                                                           quantity
                                                           )
        if attribute == 'comp_sub_total':
            product_codes_iter, value = value.split("|")
            return """sum(
                [prod_sub_total.get(prod_code,0) for prod_code in %s]
                ) %s %s""" % (
                               eval(product_codes_iter),
                               comparator,
                               value
                               )
        if attribute == 'comp_sub_total_x':
            product_codes_iter, value = value.split("|")
            return """(sum(prod_sub_total.values()) - sum(
                [prod_sub_total.get(prod_code,0) for prod_code in %s]
                )) %s %s""" % (
                               eval(product_codes_iter),
                               comparator,
                               value
                               )
        if attribute == 'web_discount':
            return "%s" % attribute
        return "order.%s %s %s" % (
                                    attribute,
                                    comparator,
                                    value)

    def evaluate(self, cursor, user,
                 expression, order, context=None):
        """
        Evaluates the expression in given environment
        @param cursor: Database Cursor
        @param user: ID of User
        @param expression: Browse record of expression
        @param order: Browse Record of sale order
        @param context: Context(no direct use).
        @return: True if evaluation succeeded
        """
        products = []   # List of product Codes
        prod_qty = {}   # Dict of product_code:quantity
        prod_unit_price = {}
        prod_sub_total = {}
        prod_discount = {}
        prod_weight = {}
        prod_net_price = {}
        prod_lines = {}
        prod_tag = {}
        web_discount = False

        for line in order.order_line:
            if line.product_id:
                product_code = line.product_id.code
                products.append(product_code)
                prod_lines[product_code] = line.product_id
                prod_tag = line.product_tags
                if line.web_discount:
                    web_discount = True
                prod_qty[product_code] = prod_qty.get(
                                            product_code, 0.00
                                                    ) + line.product_uom_qty
#                prod_net_price[product_code] = prod_net_price.get(
#                                                    product_code, 0.00
#                                                    ) + line.price_net
                prod_unit_price[product_code] = prod_unit_price.get(
                                                    product_code, 0.00
                                                    ) + line.price_unit
                prod_sub_total[product_code] = prod_sub_total.get(
                                                    product_code, 0.00
                                                    ) + line.price_subtotal
                prod_discount[product_code] = prod_discount.get(
                                                    product_code, 0.00
                                                    ) + line.discount
                prod_weight[product_code] = prod_weight.get(
                                                    product_code, 0.00
                                                    ) + line.th_weight
        return eval(expression.serialised_expr)


class PromotionsRulesActions(orm.Model):
    _inherit = 'promos.rules.actions'
    _columns = {
        'action_type': fields.selection(ACTION_TYPES, 'Action', required=True)
    }

    def on_change(self, cr, uid, ids=None, action_type=None, product_code=None,
                  arguments=None, context=None):
        res = super(PromotionsRulesActions, self).\
            on_change(cr, uid, ids, action_type=action_type,
                      product_code=product_code, arguments=arguments,
                      context=context)
        if action_type in ['prod_disc_perc_accumulated']:
            res = {'value': {'product_code': "'product_code'",
                             'arguments': "0.00"}}
        if action_type in ['tag_disc_perc', 'tag_disc_perc_accumulated']:
            res = {'value': {'product_code': "'tag_name'",
                             'arguments': "0.00"}}
        if action_type in ['categ_disc_perc', 'categ_disc_perc_accumulated']:
            res = {'value': {'product_code': "'categ_code'",
                             'arguments': "0.00"}}
        if action_type in ['brand_disc_perc', 'brand_disc_perc_accumulated']:
            res = {'value': {'product_code': "'brand_code'",
                             'arguments': "0.00"}}
        if action_type in ['web_disc_accumulated']:
            res = {'value': {'arguments': "10.00"}}
        return res

    def apply_perc_discount_accumulated(self, cursor, user, action, order_line,
                                        context=None):
        order_line_obj = self.pool.get('sale.order.line')
        final_discount = eval(action.arguments)
        if order_line.discount:
            price_discounted = order_line_obj._calc_line_base_price(
                cursor, user, order_line, context=context)
            new_price_unit = price_discounted * \
                (1 - (eval(action.arguments) / 100.0))
            final_discount = 100.0 - (new_price_unit * 100.0 /
                                      order_line.price_unit)
        if order_line.accumulated_promo:
            order_line_obj.write(cursor, user, order_line.id,
                                 {'discount': final_discount},
                                 context)
        else:
            order_line_obj.write(cursor, user, order_line.id,
                                 {'discount': final_discount,
                                  'old_discount': order_line.discount,
                                  'accumulated_promo': True},
                                 context)

    def action_tag_disc_perc_accumulated(self, cursor, user, action, order,
                                         context=None):
        """
        Action for 'Discount % on Product'
        @param cursor: Database Cursor
        @param user: ID of User
        @param action: Action to be taken on sale order
        @param order: sale order
        @param context: Context(no direct use).
        """
        for order_line in order.order_line:
            if eval(action.product_code) in order_line.product_tags:
                self.apply_perc_discount_accumulated(cursor, user, action,
                                                     order_line, context)
        return {}

    def action_categ_disc_perc_accumulated(self, cursor, user, action, order,
                                           context=None):
        for order_line in order.order_line:
            if eval(action.product_code) == \
                    order_line.product_id.categ_id.code:
                self.apply_perc_discount_accumulated(cursor, user, action,
                                                     order_line, context)
        return {}

    def action_brand_disc_perc_accumulated(self, cursor, user, action, order,
                                           context=None):
        for order_line in order.order_line:
            if eval(action.product_code) == \
                    order_line.product_id.product_brand_id.code:
                self.apply_perc_discount_accumulated(cursor, user, action,
                                                     order_line, context)
        return {}

    def action_prod_disc_perc_accumulated(self, cursor, user, action, order,
                                          context=None):
        for order_line in order.order_line:
            if order_line.product_id.code == eval(action.product_code):
                self.apply_perc_discount_accumulated(cursor, user, action,
                                                     order_line, context)

    def apply_perc_discount(self, cursor, user, action, order_line,
                            context=None):
        vals = {
            'discount': eval(action.arguments),
            'old_discount': order_line.discount,
        }
        return order_line.write(vals)

    def action_tag_disc_perc(self, cursor, user, action, order, context=None):
        """
        Action for 'Discount % on Product'
        @param cursor: Database Cursor
        @param user: ID of User
        @param action: Action to be taken on sale order
        @param order: sale order
        @param context: Context(no direct use).
        """
        for order_line in order.order_line:
            if eval(action.product_code) in order_line.product_tags:
                self.apply_perc_discount(cursor, user, action, order_line,
                                         context)
        return {}

    def action_categ_disc_perc(self, cursor, user, action, order,
                               context=None):
        for order_line in order.order_line:
            if eval(action.product_code) == \
                    order_line.product_id.categ_id.code:
                self.apply_perc_discount(cursor, user, action, order_line,
                                         context)
        return {}

    def action_brand_disc_perc(self, cursor, user, action, order,
                               context=None):
        for order_line in order.order_line:
            if eval(action.product_code) == \
                    order_line.product_id.product_brand_id.code:
                self.apply_perc_discount(cursor, user, action, order_line,
                                         context)
        return {}

    def action_web_disc_accumulated(self, cursor, user, action, order,
                               context=None):
        for order_line in order.order_line:
            if order_line.web_discount:
                self.apply_perc_discount_accumulated(cursor, user, action,
                                                     order_line, context)
        return {}
