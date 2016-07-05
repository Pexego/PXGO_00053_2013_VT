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


class ProductProductMount(models.Model):

    _name = "product.product.mount"

    product_id = fields.Many2one("product.product", "Product", required=True)
    qty = fields.Float("Qty.", required=1, default=1.0)
    name = fields.Char("Description", size=128, required=True)
    head_product_id = fields.Many2one("product.product", "Product",
                                      required=True)


class ProductTemplate(models.Model):

    _inherit = "product.template"

    custom = fields.Boolean("Custom", readonly=True)


class ProductProduct(models.Model):

    _inherit = 'product.product'

    can_mount_ids = fields.One2many(
        'product.product.mount',
        'head_product_id',
        'Can mount')

    def _update_product_prices(self, first_prod, sec_prod, product_mount):
        prod_dict = {}
        prod_dict['standard_price'] = first_prod.standard_price + \
            (sec_prod.standard_price * product_mount.qty)
        prod_dict['list_price'] = first_prod.list_price + \
            (sec_prod.list_price * product_mount.qty)
        prod_dict['list_price2'] = first_prod.list_price2 + \
            (sec_prod.list_price2 * product_mount.qty)
        prod_dict['list_price3'] = first_prod.list_price3 + \
            (sec_prod.list_price3 * product_mount.qty)
        prod_dict['pvi1_price'] = first_prod.pvi1_price + \
            (sec_prod.pvi1_price * product_mount.qty)
        prod_dict['pvi2_price'] = first_prod.pvi2_price + \
            (sec_prod.pvi2_price * product_mount.qty)
        prod_dict['pvi3_price'] = first_prod.pvi3_price + \
            (sec_prod.pvi3_price * product_mount.qty)
        return prod_dict

    def get_product_customized(self, prod_code, product_mount):
        product = self.search([('default_code', '=', prod_code)])
        if not product:
            prod_dict = {
                'type': 'product',
                'default_code': prod_code,
                'route_ids': [(6, 0,
                               [self.env.
                                ref('mrp.route_warehouse0_manufacture').id])],
                'sale_ok': False,
                'purchase_ok': False,
                'state2': 'published',
                'valuation': 'manual_periodic',
                'custom': True
            }
            bom_lines = []
            if '#' in prod_code:
                # hay varios productos
                code = prod_code.split('#')
                first_prod = self.search([('default_code', '=', code[0])])
                if '|' in code[1]:
                    sec_prod = self.search(
                        [('default_code', '=',
                          code[1][code[1].index('?')+1:code[1].index('|')])])
                else:
                    sec_prod = self.search(
                        [('default_code', '=',
                          code[1][code[1].index('?')+1:])])
                prod_dict['name'] = first_prod.name + u' - ' + sec_prod.name
                prod_dict.update(self._update_product_prices(first_prod,
                                                             sec_prod,
                                                             product_mount))
                qty = product_mount.qty
                while qty > 0:
                    bom_lines.append((0, 0,
                                      {'product_id': sec_prod.id,
                                       'product_qty': 1,
                                       'final_lot': False}))
                    qty -= 1
            else:
                first_prod = self.search([('default_code', '=',
                                           prod_code.split('|')[0])])
                prod_dict['name'] = first_prod.name
                prod_dict['standard_price'] = first_prod.standard_price
                prod_dict['list_price'] = first_prod.list_price
                prod_dict['list_price2'] = first_prod.list_price2
                prod_dict['list_price3'] = first_prod.list_price3
            bom_lines.append((0, 0,
                              {'product_id': first_prod.id,
                               'product_qty': 1,
                               'final_lot': True}))
            product = self.create(prod_dict)
            bom_list_dict = {
                'name': product.name,
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_id': product.id,
                'bom_line_ids': bom_lines,
            }
            self.env['mrp.bom'].create(bom_list_dict)
        else:
            prod_dict = {'custom': True}
            if '#' in prod_code:
                # hay varios productos
                code = prod_code.split('#')
                first_prod = self.search([('default_code', '=', code[0])])
                if '|' in code[1]:
                    sec_prod = self.search([('default_code', '=',
                                             code[1][:code[1].index('|')])])
                else:
                    sec_prod = self.search([('default_code', '=', code[1])])
                prod_dict.update(self._update_product_prices(first_prod,
                                                             sec_prod,
                                                             product_mount))
            product.write(prod_dict)
        return product
