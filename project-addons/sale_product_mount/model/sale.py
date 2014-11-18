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

    can_mount = fields.Many2one('product.product', 'Mount')

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
        res['domain']['can_mount'] = [('id', 'in',
                                       [x.id for x in prod.can_mount_ids])]
        return res


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.one
    def order_reserve(self):
        prod_obj = self.env['product.product']
        final_lines = []
        for line in self.order_line:
            if line.can_mount:
                if not line.can_mount.default_code or not \
                        line.product_id.default_code:
                    raise exceptions.except_orm(
                        _('Error'),
                        _('One of the products not have default code'))
                final_prod = prod_obj.search(
                    [('default_code', '=',
                      line.product_id.default_code +
                      line.can_mount.default_code
                      )])
                if not final_prod:
                    final_prod = self.env['product.product'].create_mounted_product(
                        line.product_id, line.can_mount)

                final_line_dict = {
                    'product_id': final_prod.id,
                    'order_id': self.id,
                    'price_unit': line.can_mount.list_price + line.price_unit,
                    'purchase_price': line.can_mount.standard_price +
                    line.purchase_price,
                    'delay': max([line.can_mount.sale_delay, line.delay]),
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': final_prod.uom_id.id
                }
                final_line = self.env['sale.order.line'].create(
                    final_line_dict)
                if final_prod.qty_available <= 0:
                    bom_id = final_prod.bom_ids[0]
                    for i in range(int(final_line.product_uom_qty - final_prod.qty_available)):
                        mrp_dict = {
                            'product_id': final_prod.id,
                            'bom_id': bom_id.id,
                            'product_uom': bom_id.product_uom.id,
                            'product_qty': 1,
                        }
                        self.env['mrp.production'].create(mrp_dict)
                final_lines.append(final_line.id)

            else:
                final_lines.append(line.id)
        for line in self.order_line:
            if line.id not in final_lines:
                line.unlink()
        self.write({'order_line': [(6, 0, final_lines)]})
        super(SaleOrder, self).order_reserve()
