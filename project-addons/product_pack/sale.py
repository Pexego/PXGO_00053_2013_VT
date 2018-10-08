# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp.osv import fields
from openerp import api, models


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    _columns = {
        'pack_depth': fields.integer(
            'Depth', required=True,
            help='Depth of the product if it is part of a pack.'
        ),
        'pack_parent_line_id': fields.many2one(
            'sale.order.line', 'Pack',
            help='The pack that contains this product.', ondelete="cascade"
        ),
        'pack_child_line_ids': fields.one2many(
            'sale.order.line', 'pack_parent_line_id', 'Lines in pack'),
    }
    _defaults = {
        'pack_depth': 0,
    }

    def invoice_line_create(self, cr, uid, ids, context=None):
        no_pack_ids = []
        for line in self.browse(cr, uid, ids, context):
            if not line.pack_depth > 0:
                no_pack_ids.append(line.id)
        return super(sale_order_line, self).invoice_line_create(cr, uid, no_pack_ids, context)

    @api.multi
    def write(self, vals):
        res = super(sale_order_line, self).write(vals)
        for line in self:
            line.refresh()
            if line.pack_child_line_ids and (not line.product_id or not line.
                                             product_id.pack_line_ids):
                for cline in line.pack_child_line_ids:
                    cline.pack_depth = 0
                    cline.pack_parent_line_id = False
        return res

    @api.multi
    def pack_in_moves(self, product_ids):
        is_in_list = True
        for child in self.pack_child_line_ids:
            if child.pack_child_line_ids:
                if not child.pack_in_moves(product_ids):
                    is_in_list = False
            else:
                if child.product_id.id not in product_ids:
                    is_in_list = False
        return is_in_list


class sale_order(models.Model):
    _inherit = 'sale.order'

    def create(self, cr, uid, vals, context=None):
        result = super(sale_order, self).create(cr, uid, vals, context)
        self.expand_packs(cr, uid, [result], context)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        result = super(sale_order, self).write(cr, uid, ids, vals, context)
        self.expand_packs(cr, uid, ids, context)
        return result

    def copy(self, cr, uid, id, default={}, context=None):
        line_obj = self.pool.get('sale.order.line')
        result = super(sale_order, self).copy(cr, uid, id, default, context)
        sale = self.browse(cr, uid, result, context)
        self.unlink_pack_components(cr, uid, sale.id, context)
        self.expand_packs(cr, uid, sale.id, context)
        return result

    def unlink_pack_components(self, cr, uid, sale_id, context=None):
        search_vals = [('order_id', '=', sale_id), ('pack_parent_line_id', '!=', None),
                       ('pack_child_line_ids', '=', None)]
        unlink_lines = self.pool.get('sale.order.line').search(cr, uid,  search_vals,
                                                               context=context)
        if unlink_lines:
            self.pool.get('sale.order.line').unlink(cr, uid, unlink_lines, context)
            self.unlink_pack_components(cr, uid, sale_id, context)
        else:
            return

    def expand_packs(self, cr, uid, ids, context={}, depth=1):
        if type(ids) in [int, long]:
            ids = [ids]
        if depth == 10:
            return
        updated_orders = []
        for order in self.browse(cr, uid, ids, context):

            fiscal_position = (
                order.fiscal_position
                and self.pool.get('account.fiscal.position').browse(
                    cr, uid, order.fiscal_position.id, context
                )
                or False
            )
            """
            The reorder variable is used to ensure lines of the same pack go
            right after their parent. What the algorithm does is check if the
            previous item had children. As children items must go right after
            the parent if the line we're evaluating doesn't have a parent it
            means it's a new item (and probably has the default 10 sequence
            number - unless the appropiate c2c_sale_sequence module is
            installed). In this case we mark the item for reordering and
            evaluate the next one. Note that as the item is not evaluated and
            it might have to be expanded it's put on the queue for another
            iteration (it's simple and works well). Once the next item has been
            evaluated the sequence of the item marked for reordering is updated
            with the next value.
            """
            sequence = -1
            reorder = []
            last_had_children = False
            for line in order.order_line:
                if last_had_children and not line.pack_parent_line_id:
                    reorder.append(line.id)
                    if (
                        line.product_id.pack_line_ids
                        and order.id not in updated_orders
                    ):
                        updated_orders.append(order.id)
                    continue

                sequence += 1

                if sequence > line.sequence:
                    self.pool.get('sale.order.line').write(
                        cr, uid, [line.id], {'sequence': sequence, }, context)
                else:
                    sequence = line.sequence

                if line.state != 'draft':
                    continue
                if not line.product_id:
                    continue

                """ If pack was already expanded (in another create/write
                operation or in a previous iteration) don't do it again. """
                if line.pack_child_line_ids:
                    last_had_children = True
                    continue
                last_had_children = False

                for subline in line.product_id.pack_line_ids:
                    sequence += 1

                    subproduct = subline.product_id
                    quantity = subline.quantity * line.product_uom_qty

                    if line.product_id.pack_fixed_price:
                        price = 0.0
                        discount = 0.0
                    else:
                        pricelist = order.pricelist_id.id
                        price = self.pool.get('product.pricelist').price_get(
                            cr, uid, [pricelist], subproduct.id, quantity,
                            order.partner_id.id, {
                                'uom': subproduct.uom_id.id,
                                'date': order.date_order,
                                }
                            )[pricelist]
                        discount = line.discount

                    # Obtain product name in partner's language
                    ctx = {'lang': order.partner_id.lang}
                    subproduct_name = self.pool.get('product.product').browse(
                        cr, uid, subproduct.id, ctx).name

                    tax_ids = self.pool.get('account.fiscal.position').map_tax(
                        cr, uid, fiscal_position, subproduct.taxes_id)

                    if subproduct.uos_id:
                        uos_id = subproduct.uos_id.id
                        uos_qty = quantity * subproduct.uos_coeff
                    else:
                        uos_id = False
                        uos_qty = quantity

                    vals = {
                        'order_id': order.id,
                        'name': '%s%s' % (
                            '> ' * (line.pack_depth+1), subproduct_name
                        ),
                        'sequence': sequence,
                        'delay': subproduct.sale_delay or 0.0,
                        'product_id': subproduct.id,
                        'procurement_ids': (
                            [(4, x.id) for x in line.procurement_ids]
                        ),
                        'price_unit': price,
                        'tax_id': [(6, 0, tax_ids)],
                        'address_allotment_id': False,
                        'product_uom_qty': quantity,
                        'product_uom': subproduct.uom_id.id,
                        'product_uos_qty': uos_qty,
                        'product_uos': uos_id,
                        'product_packaging': False,
                        'discount': discount,
                        'number_packages': False,
                        'th_weight': False,
                        'state': 'draft',
                        'pack_parent_line_id': line.id,
                        'pack_depth': line.pack_depth + 1,
                    }

                    """ It's a control for the case that the
                    nan_external_prices was installed with the product pack """
                    if 'prices_used' in line:
                        vals['prices_used'] = line.prices_used
                    if line.deposit:
                        vals['deposit'] = True

                    self.pool.get('sale.order.line').create(
                        cr, uid, vals, context)
                    if order.id not in updated_orders:
                        updated_orders.append(order.id)

                for id in reorder:
                    sequence += 1
                    self.pool.get('sale.order.line').write(
                        cr, uid, [id], {'sequence': sequence, }, context)

        if updated_orders:
            """ Try to expand again all those orders that had a pack in this
            iteration. This way we support packs inside other packs. """
            self.expand_packs(cr, uid, ids, context, depth + 1)
        return
