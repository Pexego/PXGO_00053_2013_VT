##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Comunitea (<http://comunitea.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

class StockMove(models.Model):

    _inherit = "stock.move"

    @api.multi
    def _get_origin_create_date(self):
        self.ensure_one()
        if self.purchase_line_id:
            all_moves = self.env["stock.move"].\
                search([('purchase_line_id', '=',
                         self.purchase_line_id.id)],
                       order="create_date asc", limit=1)
            return all_moves.create_date
        else:
            return self.create_date
