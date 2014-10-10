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

from openerp import fields, models, api


class product_product(models.Model):

    _inherit = 'product.product'

    is_outlet = fields.Boolean('Is outlet', compute='_is_outlet')
    normal_product_id = fields.Many2one('product.product', 'normal product')
    outlet_product_ids = fields.One2many('product.product',
                                         'normal_product_id',
                                         'Outlet products')

    @api.one
    def _is_outlet(self):
        outlet_cat = self.env.ref('product_outlet.product_category_outlet')
        if self.categ_id == outlet_cat or \
                self.categ_id.parent_id == outlet_cat:
            self.is_outlet = True
        else:
            self.is_outlet = False
