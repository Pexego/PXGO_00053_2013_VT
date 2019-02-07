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


from odoo import fields, models, api


class claim_make_repair(models.TransientModel):

    @api.model
    def get_line(self):
        context = self.env.context
        return self.env['claim.line'].browse(context.get('active_id', False))

    _name = "claim.make.repair"

    line_id = fields.Many2one('claim.line', 'Line', default=get_line)

    @api.multi
    def make(self):
        repair_obj = self.env['mrp.repair']

        repair_dict = {
            'product_id': self.line_id.product_id.id,
            'product_uom': self.line_id.product_id.uom_id.id,
            'product_qty': self.line_id.product_returned_quantity,
            'partner_id': self.line_id.claim_id.partner_id.id,
            'address_id': self.line_id.claim_id.delivery_address_id.id,
            'location_id': self.line_id.claim_id.warehouse_id.lot_rma_id.id,
            'location_dest_id': self.line_id.claim_id.warehouse_id.lot_rma_id.id,
            'invoice_method': 'none',
            'partner_invoice_id': self.line_id.claim_id.partner_id.id,
        }
        repair = repair_obj.create(repair_dict)
        self.line_id.repair_id = repair
        res = self.env.ref('mrp_repair.view_repair_order_form')
        return {
            'name': 'Repair',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res.id],
            'res_model': 'mrp.repair',
            'context': "{}",
            'type': 'ir.actions.act_window',
            'res_id': repair.id
        }
