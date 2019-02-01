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

from openerp import models, api, _


class CrmClaimRma(models.Model):
    _inherit = "crm.claim"

    @api.multi
    def button_update_lines_wizard(self):
        if not self.claim_line_ids:
            return False

        wizard_model = self.env['crm_claim_update_lines.wizard']
        val = {'partner_id': self.partner_id.id}
        new = wizard_model.create(val)

        return {
            'name': _('Data update in common in all RMA lines'),
            'view_type': 'form',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'crm_claim_update_lines.wizard',
            'res_id': new.id,
            'view_id': wizard_model.id,
            'target': 'new',
        }

