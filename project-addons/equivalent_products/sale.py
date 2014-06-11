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

from openerp.osv import fields, orm
from openerp.tools.translate import _

class sale_order_line(orm.Model):

    _inherit = "sale.order.line"

    def equivalent_products(self, cr, uid, ids, context=None):
        line = self.browse(cr, uid, ids[0], context)
        tag_wiz_obj = self.pool.get('sale.equivalent.tag')
        wizard_id = self.pool.get("sale.equivalent.products").create(cr, uid, {'line_id':ids[0]}, context=context)
        for tag in line.product_id.tag_ids:
            tag_wiz_obj.create(cr, uid, {'name': tag.name, 'wiz_id': wizard_id}, context)
        return {
            'name':_("Equivalent products"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'sale.equivalent.products',
            'res_id':wizard_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }
