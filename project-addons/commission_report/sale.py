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


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.model
    def _default_agent(self):
        agent = self.env['res.partner']
        if self.env.context.get('partner_id'):
            partner = self.env['res.partner'].\
                browse(self.env.context['partner_id'])
            if partner.agents:
                agent = partner.agents[0]
        return agent

    @api.model
    def _default_commission(self):
        commission = self.env["sale.commission"]
        if self.env.context.get('partner_id'):
            partner = self.env['res.partner'].browse(
                self.env.context['partner_id'])
            if partner.agents:
                commission = partner.agents[0].commission
        return commission

    agent = fields.Many2one("res.partner", "Agent", ondelete="restrict",
                            domain=[('agent', '=', True)],
                            default=_default_agent)
    commission = fields.Many2one("sale.commission", "Commission",
                                 ondelete="restrict",
                                 default=_default_commission)

    @api.onchange('agent')
    def onchange_agent(self):
        self.commission = self.agent.commission.id

    @api.model
    def create(self, vals):
        new_id = super(SaleOrderLine, self).create(vals)
        if vals.get('agent', False):
            agent = self.env["res.partner"].browse(vals["agent"])
            self.env["sale.order.line.agent"].\
                create({'sale_line': new_id.id,
                        'agent': vals['agent'],
                        'commission': vals.get('commission', False) or
                        agent.commission.id})

        return new_id

    @api.multi
    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        if vals.get('agent', False) or vals.get('commission', False):
            for line in self:
                if line.agents:
                    if vals.get('agent', False):
                        agent = self.env["res.partner"].browse(vals["agent"])
                        line.agents[0].agent = vals['agent']
                        line.agents[0].commission = vals.get('commission',
                                                             False) \
                            or agent.commission.id
                    elif vals.get('commission', False):
                        line.agents[0].commission = vals['commission']
                elif vals.get('agent', False):
                    agent = self.env["res.partner"].browse(vals["agent"])
                    self.env["sale.order.line.agent"].\
                        create({'sale_line': line.id,
                                'agent': vals['agent'],
                                'commission': vals.get('commission', False) or
                                agent.commission.id})

        return res
