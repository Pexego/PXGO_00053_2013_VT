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
import openerp.addons.decimal_precision as dp


class product_product(models.Model):

    _inherit = 'product.product'

    is_outlet = fields.Boolean('Is outlet', compute='_is_outlet')
    outlet_product_id = fields.Many2one('product.product', 'Outlet product')

    @api.one
    def _is_outlet(self):
        if self.categ_id == self.env.ref('product_outlet.product_category_outlet'):
            self.is_outlet = True
        else:
            self.is_outlet = False
