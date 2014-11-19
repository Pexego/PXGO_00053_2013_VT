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
from openerp import models, fields, api, exceptions, _


class CreateMountedProd(models.TransientModel):

    _name = "mrp.mounted.product.create.wizard"

    mount_product = fields.Many2one('product.product',
                                    'Mount product', required=True)
    mounted_product = fields.Many2one('product.product',
                                      'mounted product', required=True)

    @api.multi
    def create_product(self):
        if not self.mount_product.default_code or not \
                self.mounted_product.default_code:
            raise exceptions.except_orm(_('Code error'),
                                        _('One of the products not have ref.'))
        prod_created = self.env['product.product'].search(
            [('default_code', '=',
              self.mount_product.default_code +
              self.mounted_product.default_code)])
        if prod_created:
            raise exceptions.except_orm(_('Product error'),
                                        _('The mounted product alredery exists'))
        self.env['product.product'].create_mounted_product(
            self.mount_product, self.mounted_product)
        if self.mounted_product not in self.mount_product:
            self.mount_product.can_mount_ids = [(4,
                                                 self.mounted_product.id)]
        return True
