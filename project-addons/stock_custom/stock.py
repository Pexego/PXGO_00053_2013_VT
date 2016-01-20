# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos
#    $Carlos Lombardía Rodríguez <carlos@comunitea.com>$
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

class stock_picking(models.Model):
    _inherit = "stock.picking"

    internal_notes = fields.Text("Internal Notes")

    def action_assign(self, cr, uid, ids, context=None):
        res = super(stock_picking, self).action_assign(cr, uid, ids,
                                                       context=context)
        for id in ids:
            obj = self.browse(cr, uid, id)
            if obj.claim_id:
                obj.force_assign()

        return True

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        res = super(stock_picking, self)._get_invoice_vals(cr, uid, key,
                                       inv_type, journal_id, move, context=None)
        res['internal_notes'] = move.procurement_id.sale_line_id.order_id.internal_notes
        return res

class stock_move(models.Model):
    _inherit = "stock.move"

    def _prepare_picking_assign(self, cr, uid, move, context=None):
        res = super(stock_move, self)._prepare_picking_assign(cr, uid, move,
                                                              context=context)
        res['internal_notes'] = move.procurement_id.sale_line_id.order_id.internal_notes
        return res