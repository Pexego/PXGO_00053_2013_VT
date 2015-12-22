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
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api

class mrp_repair(models.Model):
    _inherit = "mrp.repair"

    @api.multi
    def action_repair_end(self):
        res = super(mrp_repair, self).action_repair_end()
        order_obj = self.browse(self.id)
        claim_line_obj = self.env['claim.line'].browse(self.claim_id.id)
        claim_obj = self.env['crm.claim'].browse(claim_line_obj.id)

        if claim_obj.claim_type == u'customer':
            for operation in order_obj.operations.ids:
                operation_obj = order_obj.operations.browse(operation)
                if operation_obj.type == u'add':
                    if operation_obj.to_invoice == False:
                        product_obj = self.env['product.product'].browse(operation_obj.product_id.id)
                        claim_obj.rma_cost += product_obj.standard_price

        return True
