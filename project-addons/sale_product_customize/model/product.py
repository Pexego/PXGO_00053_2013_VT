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

from openerp import models, fields


class ProductProduct(models.Model):

    _inherit = 'product.product'

    can_mount_ids = fields.Many2many(
        'product.product',
        'mount_products_rel',
        'product_id',
        'mounted_product_id',
        'Can mount')
    mounted_in_ids = fields.Many2many(
        'product.product',
        'mount_products_rel',
        'mounted_product_id',
        'product_id',
        'Mounted in')

    def create_mounted_product(self, mount_product, mounted_product):
        prod_dict = {
            'name': mount_product.name + ' - ' +
            mounted_product.name,
            'type': 'product',
            'default_code':
                mount_product.default_code +
                mounted_product.default_code,
            'route_ids':
                [(6, 0,
                  [self.env.ref('mrp.route_warehouse0_manufacture').id])],
            'sale_ok': False,
            'purchase_ok': False,
            'state2': 'published',
            'valuation': 'manual_periodic',
        }
        final_prod = self.create(prod_dict)

        bom_list_dict = {
            'name': final_prod.name,
            'product_tmpl_id': final_prod.product_tmpl_id.id,
            'product_id': final_prod.id,
            'bom_line_ids':
                [(0, 0,
                  {'product_id': mount_product.id,
                   'product_qty': 1,
                   'final_lot': True}),
                 (0, 0,
                  {'product_id': mounted_product.id,
                   'product_qty': 1,
                   'final_lot': False})],
        }
        self.env['mrp.bom'].create(bom_list_dict)
        return final_prod
