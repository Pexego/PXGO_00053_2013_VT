# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
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

from openerp.osv import fields, orm


class sale_order_line(orm.Model):

    _inherit = "sale.order.line"

    _columns = {
        'original_line_id': fields.many2one('sale.order.line', 'Origin',
                                            ondelete='cascade'),
        'assoc_line_ids': fields.one2many('sale.order.line',
                                          'original_line_id',
                                          'Associated lines',
                                          ondelete='cascade'),
    }

    def create(self, cr, uid, vals, context=None):
        product_obj = self.pool.get('product.product')
        line_obj = self.pool.get('sale.order.line')
        uom_obj = self.pool.get('product.uom')
        fiscal_obj = self.pool.get('account.fiscal.position')
        pricelist_obj = self.pool.get('product.pricelist')

        product_id = vals.get('product_id')

        line_id = super(sale_order_line, self).create(cr, uid, vals, context)
        line = line_obj.browse(cr, uid, line_id, context)
        if product_id:
            product = product_obj.browse(cr, uid, product_id, context)
            for associated in product.associated_product_ids:
                qty = uom_obj._compute_qty(cr, uid, line.product_uom.id,
                                           line.product_uom_qty,
                                           line.product_id.uom_id.id)

                fiscal_position = (line.order_id.fiscal_position and
                                   fiscal_obj.browse(cr, uid,
                                                     line.order_id.fiscal_position.id,
                                                     context) or False)
                tax_ids = fiscal_obj.map_tax(cr, uid, fiscal_position,
                                             associated.associated_id.taxes_id)

                pricelist = line.order_id.pricelist_id.id
                price = pricelist_obj.price_get(cr, uid, [pricelist],
                                                associated.associated_id.id,
                                                associated.quantity * qty,
                                                line.order_id.partner_id.id,
                                                {
                                                'uom': associated.uom_id.id,
                                                'date':
                                                    line.order_id.date_order,
                                                }
                                                )[pricelist]
                args_line = {
                    'order_id': line.order_id.id,
                    'price_unit': price,
                    'product_uom': associated.uom_id.id,
                    'product_uom_qty': associated.quantity * qty,
                    'product_id': associated.associated_id.id,
                    'original_line_id': line_id,
                    'delay': associated.associated_id.sale_delay or 0.0,
                    'tax_id': [(6, 0, tax_ids)],
                    'agent': line.agent.id,
                    'commission': line.commission.id
                }
                new_line_id = self.create(cr, uid, args_line, context)
                new_line = self.browse(cr, uid, new_line_id, context)
                line_vals = \
                    self.product_id_change(cr, uid, [new_line_id],
                                            new_line.order_id.pricelist_id.id,
                                            new_line.product_id.id,
                                            new_line.product_uom_qty,
                                            False,
                                            new_line.product_uos_qty,
                                            False,
                                            new_line.name,
                                            new_line.order_id.partner_id.id,
                                            False, True,
                                            new_line.order_id.date_order,
                                            False,
                                            new_line.order_id.fiscal_position.id,
                                            False,
                                            context)
                line_vals = line_vals['value']
                self.write(cr, uid, [new_line_id], line_vals, context)
        return line_id

    def write(self, cr, uid, ids, vals, context=None):
        assoc_obj = self.pool.get('product.associated')
        pricelist_obj = self.pool.get('product.pricelist')
        uom_obj = self.pool.get('product.uom')
        fiscal_obj = self.pool.get('account.fiscal.position')
        if vals.get('product_id'):
            res = super(sale_order_line, self).write(cr, uid, ids, vals,
                                                     context)
            for line in self.browse(cr, uid, ids, context):
                if line.assoc_line_ids:
                    self.unlink(cr, uid,
                                [x.id for x in line.assoc_line_ids],
                                context)
                line = self.browse(cr, uid, line.id, context)
                for associated in line.product_id.associated_product_ids:
                    qty = uom_obj._compute_qty(cr, uid, line.product_uom.id,
                                               line.product_uom_qty,
                                               line.product_id.uom_id.id)

                    fiscal_position = (line.order_id.fiscal_position and
                                       fiscal_obj.browse(cr, uid,
                                                         line.order_id.fiscal_position.id,
                                                         context) or False)
                    tax_ids = fiscal_obj.map_tax(cr, uid, fiscal_position,
                                                 associated.associated_id.taxes_id)

                    pricelist = line.order_id.pricelist_id.id
                    price = pricelist_obj.price_get(cr, uid, [pricelist],
                                                    associated.associated_id.id,
                                                    associated.quantity * qty,
                                                    line.order_id.partner_id.id,
                                                    {
                                                    'uom':
                                                        associated.uom_id.id,
                                                    'date':
                                                        line.order_id.date_order,
                                                    }
                                                    )[pricelist]
                    args_line = {
                        'order_id': line.order_id.id,
                        'price_unit': price,
                        'product_uom': associated.uom_id.id,
                        'product_uom_qty': associated.quantity * qty,
                        'product_id': associated.associated_id.id,
                        'original_line_id': line.id,
                        'delay': associated.associated_id.sale_delay or 0.0,
                        'tax_id': [(6, 0, tax_ids)],
                        'agent': line.agent.id,
                        'commission': line.commission.id
                    }
                    new_line_id = self.create(cr, uid, args_line, context)
                    new_line = self.browse(cr, uid, new_line_id, context)
                    line_vals = \
                        self.product_id_change(cr, uid, [new_line_id],
                                                new_line.order_id.pricelist_id.id,
                                                new_line.product_id.id,
                                                new_line.product_uom_qty,
                                                False,
                                                new_line.product_uos_qty,
                                                False,
                                                new_line.name,
                                                new_line.order_id.partner_id.id,
                                                False, True,
                                                new_line.order_id.date_order,
                                                False,
                                                new_line.order_id.fiscal_position,
                                                False,
                                                context)
                    line_vals = line_vals['value']
                    self.write(cr, uid, [new_line_id], line_vals, context)
            return res

        if vals.get('product_uom_qty'):
            for line in self.browse(cr, uid, ids, context):
                if line.assoc_line_ids:
                    diff = vals.get('product_uom_qty', line.product_uom_qty) \
                        - line.product_uom_qty

                    for assoc_line in line.assoc_line_ids:
                        association_id = assoc_obj.search(cr, uid,
                                                          [('product_id', '=',
                                                            line.product_id.id
                                                            ),
                                                           ('associated_id',
                                                            '=',
                                                            assoc_line.product_id.id)],
                                                          context=context)
                        association = assoc_obj.browse(cr, uid,
                                                       association_id[0],
                                                       context)
                        quantity = diff * association.quantity
                        self.write(cr, uid, [assoc_line.id],
                                   {'product_uom_qty':
                                       (assoc_line.product_uom_qty + quantity)
                                    },
                                   context)
        return super(sale_order_line, self).write(cr, uid, ids, vals, context)
