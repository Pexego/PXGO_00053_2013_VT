# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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

from openerp import models, fields, exceptions, api, _


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    mounted_in = fields.Many2one('product.product', 'Mounted in')

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None):

        prod = self.pool.get('product.product').browse(cr, uid, product,
                                                       context)

        res = super(SaleOrderLine, self).product_id_change(
            cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name,
            partner_id, lang, update_tax, date_order, packaging,
            fiscal_position, flag, context)
        res['domain']['mounted_in'] = [('id', 'in',
                                        [x.id for x in prod.mounted_in_ids])]
        return res


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.one
    def order_reserve(self):
        prod_obj = self.env['product.product']
        final_lines = []
        mounted_in_lines = []
        for line in self.order_line:
            if line.mounted_in:
                mount_line = self.env['sale.order.line'].search(
                    [('order_id', '=', self.id),
                     ('product_id', '=', line.mounted_in.id)])
                if not mount_line:
                    raise exceptions.except_orm(
                        _('Error'),
                        _('Not found the product %s in the order') %
                        line.mounted_in.name)
                assert len(mount_line) == 1
                if not line.mounted_in.default_code or not \
                        line.product_id.default_code:
                    raise exceptions.except_orm(
                        _('Error'),
                        _('One of the products not have default code'))
                final_prod = prod_obj.search(
                    [('default_code', '=',
                      line.mounted_in.default_code +
                      line.product_id.default_code)])
                if not final_prod:
                    # crear producto
                    prod_dict = {
                        'name': line.mounted_in.name + ' - ' +
                        line.product_id.name,
                        'type': 'product',
                        'default_code':
                            line.mounted_in.default_code +
                            line.product_id.default_code,
                        'route_ids':
                            [(6, 0,
                              [self.env.ref('mrp.route_warehouse0_manufacture').id])],
                        'sale_ok': False,
                        'purchase_ok': False,
                        'state2': 'published',
                        'valuation': 'manual_periodic',
                    }
                    final_prod = prod_obj.create(prod_dict)
                    final_qty = min([mount_line.product_uom_qty,
                                     line.product_uom_qty])
                    bom_list_dict = {
                        'name': final_prod.name,
                        'product_tmpl_id': final_prod.product_tmpl_id.id,
                        'product_id': final_prod.id,
                        'bom_line_ids':
                            [(0, 0,
                              {'product_id': line.mounted_in.id,
                               'product_qty':
                                   mount_line.product_uom_qty/final_qty}),
                             (0, 0,
                              {'product_id': line.product_id.id,
                               'product_qty':
                                   line.product_uom_qty/final_qty})],
                    }
                    self.env['mrp.bom'].create(bom_list_dict)
                final_line_dict = {
                    'product_id': final_prod.id,
                    'order_id': self.id,
                    'price_unit': mount_line.price_unit + line.price_unit,
                    'purchase_price': mount_line.purchase_price +
                    line.purchase_price,
                    'delay': max([mount_line.delay, line.delay]),
                    'product_uom_qty':
                        min([mount_line.product_uom_qty,
                             line.product_uom_qty]),
                    'product_uom': final_prod.uom_id.id
                }
                final_line = self.env['sale.order.line'].create(
                    final_line_dict)
                if final_prod.qty_available <= 0:
                    bom_id = final_prod.bom_ids[0]
                    mrp_dict = {
                        'product_id': final_prod.id,
                        'bom_id': bom_id.id,
                        'product_uom': bom_id.product_uom.id,
                        'product_qty': final_line.product_uom_qty,
                    }
                    self.env['mrp.production'].create(mrp_dict)
                final_lines.append(final_line.id)

                mounted_in_lines.append(mount_line[0].id)
            else:
                final_lines.append(line.id)
        final_lines = [x for x in final_lines if x not in mounted_in_lines]
        for line in self.order_line:
            if line.id not in final_lines:
                line.unlink()
        self.write({'order_line': [(6, 0, final_lines)]})
        super(SaleOrder, self).order_reserve()
