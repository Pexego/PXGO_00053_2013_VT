# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sanchez <kiko@comunitea.com>$
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

from openerp import models, fields, api, exceptions
from openerp.exceptions import ValidationError

class mrp_repair_fees(models.Model):

    _inherit ="mrp.repair.fee"

    @api.multi
    @api.constrains('product_id')
    def _check_duplicate_fees(self):

        line2 = self.env['mrp.repair.fee'].search([('repair_id', '=', self.repair_id.id),('product_id.shipping_balance','=','true')])
        if len(line2) > 1:
            raise ValidationError("Shipping Balance must be unique")

class mrp_repair(models.Model):

    _inherit = "mrp.repair"

    shipping_balance = fields.Boolean("Shipping Balance", default=False)

    @api.multi
    def action_invoice_create(self, group=False):

        res = super(mrp_repair, self).action_invoice_create(group)
        for repair in self:
            for line in repair.fees_lines:
                if line.product_id.shipping_balance:
                    shipping_vals = {
                        'partner_id': line.repair_id.partner_id.id,
                        'repair_id': line.repair_id.id,
                        'aproved': True,
                        'amount': line.price_unit,
                        'balance': True,
                        }
                    line2 = self.env['shipping.balance'].search([('repair_id', '=', line.repair_id.id)])
                    if line2:
                        line2.unlink()
                    else:
                        self.env['shipping.balance'].create(shipping_vals)
                    repair.shipping_balance=True
        return res



    @api.multi
    def unlink(self):

        line2 = self.env['shipping.balance'].search([('repair_id', '=', self.id)])
        if line2:
            line2.unlink()


        res = super(mrp_repair, self).unlink()
