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

from openerp import models, fields, api


class MrpCustomizationWizard(models.TransientModel):

    _name = "mrp.customization.wizard"

    product_id = fields.Many2one('product.product', 'Product')
    qty = fields.Float('Quantity')
    customization_type = fields.Many2one('mrp.customize.type', 'Type')
    product_uom = fields.Many2one('product.uom', 'UoM')

    @api.one
    def create_customization(self):
        bom = self.env['mrp.bom'].search([('product_id', '=', self.product_id.id)])
        bom_id = bom and bom[0].id or False
        if not bom_id:
            bom_list_dict = {
                'name': self.product_id.name,
                'product_tmpl_id': self.product_id.product_tmpl_id.id,
                'product_id': self.product_id.id,
                'bom_line_ids':
                    [(0, 0,
                      {'product_id': self.product_id.id,
                       'product_qty': 1,
                       'final_lot': True})],
            }
            bom_id = self.env['mrp.bom'].create(bom_list_dict).id
        mrp_args = {
            'type_id': self.customization_type.id,
            'product_id': self.product_id.id,
            'bom_id': bom_id,
            'product_uom': self.product_uom.id,
            'product_qty': self.qty,
        }
        production = self.env['mrp.production'].create(mrp_args)
        production.signal_workflow('button_confirm')

        return True
