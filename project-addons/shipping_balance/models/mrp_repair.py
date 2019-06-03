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
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError


class MrpRepairFees(models.Model):

    _inherit = 'mrp.repair.fee'

    @api.multi
    @api.constrains('product_id')
    def _check_duplicate_fees(self):

        line2 = self.env['mrp.repair.fee'].search([('repair_id', '=', self.repair_id.id),
                                                   ('product_id.shipping_balance', '=', 'true')])
        if len(line2) > 1:
            raise ValidationError("Shipping Balance must be unique")

    @api.multi
    def order_repair(self, data):
        product_id = self.env['product.product'].search([('is_repair', '=', True)])
        if 'product_id' in data and data['product_id'] in product_id.ids:
            if self.id:
                rma_number = self.repair_id.claim_id.number
                product_name = self.repair_id.product_id.name
            else:
                order_repair = self.env['mrp.repair'].browse(data['repair_id'])
                rma_number = order_repair.claim_id.number
                product_name = order_repair.product_id.name
            if rma_number:
                data['name'] += u', ' + rma_number + u' \n Prod.: ' + product_name
        return data

    @api.multi
    def write(self, data):
        data_mod = self.order_repair(data)
        res = super(MrpRepairFees, self).write(data_mod)
        return res

    @api.model
    def create(self, data):
        data_mod = self.order_repair(data)
        res = super(MrpRepairFees, self).create(data_mod)
        return res


class MrpRepair(models.Model):

    _inherit = 'mrp.repair'

    shipping_balance = fields.Boolean("Shipping Balance", default=False)

    @api.multi
    def action_invoice_create(self, group=False):

        res = super(MrpRepair, self).action_invoice_create(group)
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
                    repair.shipping_balance = True
        return res

    @api.multi
    def unlink(self):

        line2 = self.env['shipping.balance'].search([('repair_id', '=', self.id)])
        if line2:
            line2.unlink()

        res = super(MrpRepair, self).unlink()
