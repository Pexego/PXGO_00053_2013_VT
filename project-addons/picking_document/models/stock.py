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

from odoo import fields, api, models, _


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    document_ids = fields.Many2many(
        'stock.document',
        'document_picking_rel',
        'document_id',
        'picking_id',
        'Documents')

    qty = fields.Integer('qty', compute='_calculate_qty')

    @api.one
    def _calculate_qty(self):
        picking_name = self.name
        self.qty = sum(move_lines.product_uom_qty for move_lines in self.move_lines)
