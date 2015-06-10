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

from openerp import models, fields, api
from datetime import timedelta, date


class SaleCommissionMakeSettle(models.TransientModel):

    _inherit = "sale.commission.make.settle"

    def _get_line_to_settle(self, agent, date_to_agent):
        agent_line_obj = self.env['account.invoice.line.agent']
        agent_lines = agent_line_obj.search([('invoice_date', '<',
                                              date_to_agent),
                                             ('agent', '=', agent.id),
                                             ('settled', '=', False),
                                             ('invoice.state', '=', 'paid')],
                                            order='invoice_date')
        return agent_lines

    @api.multi
    def action_settle(self):
        self.ensure_one()
        settlement_obj = self.env['sale.commission.settlement']
        settlement_line_obj = self.env['sale.commission.settlement.line']
        if not self.agents:
            self.agents = self.env['res.partner'].search(
                [('agent', '=', True)])
        date_to = fields.Date.from_string(self.date_to)
        for agent in self.agents:
            date_to_agent = self._get_period_start(agent, date_to)
            # Get non settled invoices
            agent_lines = self._get_line_to_settle(agent, date_to_agent)
            if agent_lines:
                pos = 0
                sett_to = fields.Date.to_string(date(year=1900, month=1,
                                                     day=1))
                while pos < len(agent_lines):
                    if agent_lines[pos].invoice_date > sett_to:
                        sett_from = self._get_period_start(
                            agent, agent_lines[pos].invoice_date)
                        sett_to = fields.Date.to_string(
                            self._get_next_period_date(agent, sett_from) -
                            timedelta(days=1))
                        sett_from = fields.Date.to_string(sett_from)
                        settlement = settlement_obj.create(
                            {'agent': agent.id,
                             'date_from': sett_from,
                             'date_to': sett_to})
                    settlement_line_obj.create(
                        {'settlement': settlement.id,
                         'agent_line': [(6, 0, [agent_lines[pos].id])]})
                    pos += 1
        return True
