# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
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

from openerp import models, api, fields


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.one
    @api.depends('invoice_line.agents.agent')
    def _get_agents_str(self):
        agents = self.env["res.partner"]
        for line in self.invoice_line:
            for agent_line in line.agents:
                agents += agent_line.agent

        self.agents_str = u", ".join([x.name for x in agents])

    agents_str = fields.Char("Agents", compute='_get_agents_str',
                             readonly=True, store=True)

    @api.multi
    def unlink(self):
        for invoic in self:
            if self.state == 'draft':
                settlements = self.env['sale.commission.settlement'].search(
                    [('invoice', '=', invoic.id)])
                if settlements:
                    settlements.write({'state': 'except_invoice'})
        return super(AccountInvoice, self).unlink()
