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
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, api


class MrpRepair(models.Model):
    _inherit = 'mrp.repair'

    _order = 'id desc'

    @api.multi
    def action_repair_end(self):
        res = super(MrpRepair, self).action_repair_end()
        order_obj = self.browse(self.id)
        claim_line_obj = self.env['claim.line'].browse(self.claim_id.id)
        claim_obj = self.env['crm.claim'].browse(claim_line_obj.id)

        if claim_obj.claim_type == u'customer':
            for operation in order_obj.operations.ids:
                operation_obj = order_obj.operations.browse(operation)
                if operation_obj.type == u'add':
                    if operation_obj.state != '2binvoiced':
                        product_obj = self.env['product.product'].\
                            browse(operation_obj.product_id.id)
                        claim_obj.rma_cost += product_obj.standard_price

        return res

    @api.multi
    def action_invoice_create(self, group=False):
        res = super(MrpRepair, self).action_invoice_create(group=group)
        for repair_id in res:
            invoice = self.env['account.invoice'].browse(res[repair_id])
            repair = self.browse(repair_id)
            partner = repair.partner_id
            inv_vals = {
                'payment_term_id': partner.property_payment_term_id.id,
                'payment_mode_id': partner.customer_payment_mode_id.id,
                'partner_bank_id': partner.bank_ids and
                partner.bank_ids[0].id or False
            }
            invoice.write(inv_vals)

        return res

    @api.model
    def calculate_pricelist(self, data):
        partner = self.env["res.partner"].browse(data['partner_id'])
        if partner.property_product_pricelist.id:
            pricelist = partner.property_product_pricelist.id
        else:
            # Product_pricelist default id -> Public Pricelist
            pricelist = self.env.ref('product.list0').id
        return pricelist

    @api.multi
    def write(self, data):
        if 'partner_id' in data:
            data['pricelist_id'] = self.calculate_pricelist(data)
        res = super(MrpRepair, self).write(data)
        return res

    @api.model
    def create(self, data):
        data['pricelist_id'] = self.calculate_pricelist(data)
        res = super(MrpRepair, self).create(data)
        return res

