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

from openerp import models, fields, api


class CrmClaimRma(models.Model):

    _inherit = "crm.claim"
    _order = "number desc"

    agent = fields.Many2one('res.partner', 'Agent',
                               domain="[('agent', '=', True)]")
    name = fields.Selection([('return', 'Return'),
                             ('rma', 'RMA')], 'Claim Subject',
                            required=True, default='rma')
    priority = fields.Selection(default=0)

    def onchange_partner_id(self, cr, uid, ids, partner_id, email=False,
                            context=None):
        res = super(CrmClaimRma, self).onchange_partner_id(cr, uid, ids,
                                                           partner_id,
                                                           email=email,
                                                           context=context)
        if partner_id:
            partner = self.pool["res.partner"].browse(cr, uid, partner_id)
            if partner.agents:
                res['value']['agent'] = partner.agents[0].id

        return res


class CrmClaimLine(models.Model):

    _inherit = "claim.line"

    name = fields.Char(required=False)

    @api.multi
    def action_split(self):
        for line in self:
            if line.product_returned_quantity > 1:
                for x in range(1,int(line.product_returned_quantity)):
                    line.copy(default={'product_returned_quantity': 1.0})
                line.product_returned_quantity = 1
        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    @api.multi
    def create_repair(self):
        self.ensure_one()
        wzd = self.env["claim.make.repair"].create({'line_id': self.id})
        res = wzd.make()
        return res
