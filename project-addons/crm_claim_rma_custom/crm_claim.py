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
from datetime import datetime


class CrmClaimRma(models.Model):

    _inherit = "crm.claim"
    _order = "id desc"

    name = fields.Selection([('return', 'Return'),
                             ('rma', 'RMA')], 'Claim Subject',
                            required=True, default='rma')
    # priority = fields.Selection(default=0)
    priority = fields.Selection(default=0,
        selection=[('1', 'High'),
                   ('2', 'Critical')])
    comercial = fields.Many2one("res.users",string="Comercial")
    # date_received = fields.Datetime('Received Date', default=lambda *a:datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    date_received = fields.Datetime('Received Date')
    aditional_notes = fields.Text("Aditional Notes")

    def onchange_partner_id(self, cr, uid, ids, partner_id, email=False,
                            context=None):
        res = super(CrmClaimRma, self).onchange_partner_id(cr, uid, ids,
                                                           partner_id,
                                                           email=email,
                                                           context=context)
        if partner_id:
            partner = self.pool["res.partner"].browse(cr, uid, partner_id)
            if partner.user_id:
                res['value']['comercial'] = partner.user_id.id

        return res

    def onchange_name(self, cr, uid, ids, name, context=None):
        if name == 'return':
            return {'value': {'invoice_type': 'refund'}}
        elif name == 'rma':
            return {'value': {'invoice_type': 'invoice'}}

    @api.model
    def create(self, vals):
        if vals.get('name', False):
            vals['name'] = vals['name'].split(' ')[0]
        return super(CrmClaimRma, self).create(vals)


class CrmClaimLine(models.Model):

    _inherit = "claim.line"

    name = fields.Char(required=False)
    invoice_id = fields.Many2one("account.invoice", string="Invoice")

    @api.model
    def create(self, vals):
        if 'substate_id' not in vals.keys():
            vals['substate_id'] = self.env.ref(
                'crm_claim_rma_custom.substate_due_receive').id
        return super(CrmClaimLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'repair_id' in vals.keys():
            vals['substate_id'] = self.env.ref(
                'crm_claim_rma_custom.substate_repaired').id
        return super(CrmClaimLine, self).write(vals)

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
