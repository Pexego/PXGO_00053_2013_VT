# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Visiotech All Rights Reserved
#    $Anthonny Contreras Vargas <acontreras@visiotechsecurity.com>$
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

from odoo import models, api, fields


class CrmClaimUpdateLines(models.TransientModel):
    _name = 'crm_claim_update_lines.wizard'

    substate_id = fields.Many2one('substate.substate', string='substate_id')
    invoice_id = fields.Many2one('account.invoice', string='invoice_id')
    partner_id = fields.Many2one('res_partner', readonly=True)
    claim_origine = fields.Selection([('broken_down', 'Broken down product'),
                                      ('not_appropiate', 'Not appropiate product'),
                                      ('cancellation', 'Order cancellation'),
                                      ('damaged', 'Damaged delivered product'),
                                      ('error', 'Shipping error'),
                                      ('exchange', 'Exchange request'),
                                      ('lost', 'Lost during transport'),
                                      ('other', 'Other')
                                      ], 'Claim Subject')

    @api.multi
    def button_update_lines(self):
        model = self.env.context['active_model']
        crm_claim_id = self.env.context['active_id']
        obj_crm_claim = self.env[model].browse(crm_claim_id)
        vals = {}

        for rma_line in obj_crm_claim.claim_line_ids:
            if self.substate_id.id:
                vals['substate_id'] = self.substate_id.id
            if self.claim_origine:
                vals['claim_origine'] = self.claim_origine
            if self.invoice_id:
                vals['invoice_id'] = self.invoice_id.id

            rma_line.write(vals)
