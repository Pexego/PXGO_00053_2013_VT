# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Carlos Lombardía <carlos@comunitea.com>$
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
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, _, api, exceptions


class purchase_order(models.Model):

    _inherit = "purchase.order"

    def action_cancel(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('stock.move')
        for purchase in self.browse(cr, uid, ids, context=context):
            move_ids = move_obj.search(cr, uid, [('purchase_line_id', 'in', purchase.order_line.ids)], context=context)
            for move in move_obj.browse(cr, uid, move_ids):
                if move.state == 'done':
                    raise exceptions.UserError(
                        _('Unable to cancel the purchase order %s.') % (purchase.name),
                        _('You have already received some goods for it.  '))
                else:
                    move.state = 'cancel'

        res = super(purchase_order, self).action_cancel(cr, uid, ids, context=context)

        return res

    @api.multi
    @api.depends('order_line.date_planned')
    def _minimum_planned_date(self):
        for purchase in self:
            if purchase.order_line:
                min_date=purchase.order_line[0].date_planned
                for line in purchase.order_line:
                    if line.order_id.state == 'cancel':
                        continue
                    if line.date_planned < min_date:
                        min_date=line.date_planned
                purchase.minimum_planned_date = min_date

    @api.multi
    def _set_minimum_planned_date(self):
        for po in self:
            po.order_line.write({'date_planned': po.minimum_planned_date})

    minimum_planned_date = fields.Datetime(compute="_minimum_planned_date", inverse="_set_minimum_planned_date",
            string='Expected Date', index=True, help="This is computed as the minimum scheduled date of all purchase order lines' products.",
            store=True)
    manufacture_date = fields.Date("Manufacture Date", help="Date when it was manufactured")
    prepared_merchandise_date = fields.Date("Prepared Merchandise Date", help="Date when the merchandise was prepared")
    estimated_arrival_date = fields.Date("Estimated Arrival Date", help="Date when the merchandise will arrive approximately")
    telex_release = fields.Boolean("Telex Release", help="It indicates that Telex release is necessary")
    end_manufacture = fields.Date("Ending Date Of Manufacture")
    sale_notes = fields.Text("Purchase Sale Notes")
    remark = fields.Char("Remark")
