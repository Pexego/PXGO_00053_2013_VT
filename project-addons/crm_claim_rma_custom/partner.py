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

from openerp import models, fields


class ResPartner(models.Model):

    _inherit = "res.partner"

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
               context=None, count=False):
        """Si recibimos en contexto un producto filtramos por los proveedores
           del producto"""
        if context is None:
            context = {}
        if context.get('search_product_id', False):
            supp_obj = self.pool.get('product.supplierinfo')
            product_obj = self.pool.get('product.product')
            product = product_obj.browse(cr, uid, context['search_product_id'])
            args = []
            domain = [('product_tmpl_id', '=', product.product_tmpl_id.id)]
            supp_ids = supp_obj.search(cr, uid, domain, context=context)
            ids = set()
            for supp in supp_obj.browse(cr, uid, supp_ids, context=context):
                ids.add(supp.name.id)
            ids = list(ids)
            args.append(['id', 'in', ids])
        return super(ResPartner, self).search(cr, uid, args,
                                              offset=offset,
                                              limit=limit,
                                              order=order,
                                              context=context,
                                              count=count)
