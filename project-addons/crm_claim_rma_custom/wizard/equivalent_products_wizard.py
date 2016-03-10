# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos
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


class EquivalentProductsWizard(models.TransientModel):

    _inherit = "equivalent.products.wizard"

    kitchen_stock = fields.Float("Kitchen Stock", readonly=True)

    def default_get(self, cr, uid, fields, context=None):
        res = super(EquivalentProductsWizard, self).\
            default_get(cr, uid, fields, context=context)
        if context.get('line_id'):
            claim_line_id = self.pool.get('claim.line').\
                browse(cr, uid, context['line_id'])
            res['kitchen_stock'] = claim_line_id.product_id.qty_available_wo_wh
        return res

    def onchange_product_id(self, cr, uid, ids, product_id, product_ids=[],
                            context=None):
        res = super(EquivalentProductsWizard, self).\
            onchange_product_id(cr, uid, ids, product_id, product_ids,
                                context)
        if res.get('value', False) and product_id:
            prod_obj = self.pool.get('product.product')
            prod = prod_obj.browse(cr, uid, product_id)
            res['value']['kitchen_stock'] =  prod.qty_available_wo_wh

        return res
