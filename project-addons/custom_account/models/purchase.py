# Copyright 2019 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, _, exceptions, api


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    def button_cancel(self):
        for purchase in self:
            done_moves = purchase.order_line.mapped('move_ids').\
                filtered(lambda x: x.state == 'done')
            if done_moves:
                raise exceptions.\
                    UserError(_('Unable to cancel purchase order %s as '
                                'some receptions have already been done.') %
                              (purchase.name))
            else:
                purchase.order_line.mapped('move_ids').\
                    write({'state': 'cancel'})
        super().button_cancel()

    @api.depends('order_line.date_planned')
    def _minimum_planned_date(self):
        for po in self:
            po.minimum_planned_date = min(po.order_line.mapped('date_planned'))

    @api.multi
    def _set_minimum_planned_date(self):
        for po in self:
            for line in po.order_line:
                line.date_planned = po.minimum_planned_date

    minimum_planned_date = fields.Date("Expected Date", compute="_minimum_planned_date",
                                       inverse="_set_minimum_planned_date", store=True,
                                       help="This is computed as the minimum scheduled date of all purchase order lines' products.")
    manufacture_date = fields.Date("Manufacture Date",
                                   help="Date when it was manufactured")
    prepared_merchandise_date = \
        fields.Date("Prepared Merchandise Date",
                    help="Date when the merchandise was prepared")
    estimated_arrival_date = fields.\
        Date("Estimated Arrival Date",
             help="Date when the merchandise will arrive approximately")
    telex_release = fields.\
        Boolean("Telex Release",
                help="It indicates that Telex release is necessary")
    end_manufacture = fields.Date("Ending Date Of Manufacture")
    sale_notes = fields.Text("Purchase Sale Notes")
    remark = fields.Char("Remark")
