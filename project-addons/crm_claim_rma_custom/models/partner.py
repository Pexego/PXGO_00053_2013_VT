# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from openerp import models, api


class ResPartner(models.Model):

    _inherit = "res.partner"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Si recibimos en contexto un producto filtramos por los proveedores
           del producto"""
        if self.env.context.get('search_product_id'):
            supp_obj = self.env['product.supplierinfo']
            product_obj = self.env['product.product']
            product = product_obj.browse(self.env.context['search_product_id'])
            args = []
            domain = [('product_tmpl_id', '=', product.product_tmpl_id.id)]
            supp_ids = supp_obj.search(domain)
            partners = supp_ids.mapped('name')
            args.append(['id', 'in', partners.ids])
        return super(ResPartner, self).search(args,
                                              offset=offset,
                                              limit=limit,
                                              order=order,
                                              count=count)
