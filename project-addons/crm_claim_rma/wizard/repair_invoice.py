# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from odoo import models, fields, api, exceptions, _


class RepairInvoiceFromClaim(models.TransientModel):

    _name = "mrp.repair.invoice.from.claim"

    @api.model
    def _get_repair_ids(self):
        repair_ids = []
        if self.env.context.get('active_ids', []):
            claim_ids = self.env.context['active_ids']
            for claim in self.env["crm.claim"].browse(claim_ids):
                for line in claim.claim_line_ids:
                    if line.repair_id and line.repair_id.state == "2binvoiced":
                        repair_ids.append(line.repair_id.id)
        if not repair_ids:
            raise exceptions.Warning(_("Any repair to invoice in this claim"))
        else:
            return repair_ids

    repair_ids = fields.Many2many("mrp.repair", "mrp_repair_invoice_wzd_rel",
                                  "wzd_id", "repair_id", "Repairs",
                                  default=_get_repair_ids,
                                  domain=[('state', '=', '2binvoiced')])

    @api.multi
    def action_invoice(self):
        obj = self[0]
        wzd_obj = self.env["mrp.repair.make_invoice"]
        if obj.repair_ids:
            repair_ids = [x.id for x in obj.repair_ids]
        else:
            raise exceptions.Warning(_("Any repair to invoice in this claim"))
        invoice_wzd = wzd_obj.create({'group': True})
        res = invoice_wzd.with_context(active_ids=repair_ids).make_invoices()
        return res
