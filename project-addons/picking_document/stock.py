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

from openerp import fields, api, models, _
import openerp.addons.decimal_precision as dp

class stock_picking(models.Model):

    _inherit = 'stock.picking'


    document_ids = fields.Many2many(
        'stock.document',
        'document_picking_rel',
        'document_id',
        'picking_id',
        'Documents')

    name = fields.Char('name')
    qty =fields.Integer('qty', compute='_calculate_qty')

    @api.one
    @api.depends('name')
    def _calculate_qty(self):
        picking_name = self.name
        qty_mid = self.env.cr.execute(
            """
SELECT sum(product_uom_qty)
FROM stock_move
    INNER JOIN stock_picking ON stock_move.picking_id = stock_picking.id
WHERE stock_picking.name = '"""+ picking_name + """'"""
        )
        qty_mid = self.env.cr.fetchall()
        qty123 = int(qty_mid[0][0])
        self.qty = qty123
