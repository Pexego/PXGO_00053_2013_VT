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

from openerp import SUPERUSER_ID
from openerp import models, fields, api, tools


class AccountInvoiceReportFilter(models.Model):

    _name = 'account.invoice.report.filter'
    _inherit = 'account.invoice.report'

    def _where(self, cr):
        parameters = self.pool.get('ir.config_parameter').get_param(cr, SUPERUSER_ID, 'search.default.brands')
        return "WHERE pb.name NOT IN " + str(tuple(parameters.encode('utf8').split(',')))

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            WITH currency_rate (currency_id, rate, date_start, date_end) AS (
                SELECT r.currency_id, r.rate, r.name AS date_start,
                    (SELECT name FROM res_currency_rate r2
                     WHERE r2.name > r.name AND
                           r2.currency_id = r.currency_id
                     ORDER BY r2.name ASC
                     LIMIT 1) AS date_end
                FROM res_currency_rate r
            )
            %s
            FROM (
                %s 
                %s
                %s
                %s
            ) AS sub
            JOIN currency_rate cr ON
                (cr.currency_id = sub.currency_id AND
                 cr.date_start <= COALESCE(sub.date, NOW()) AND
                 (cr.date_end IS NULL OR cr.date_end > COALESCE(sub.date, NOW())))
            
        )""" % (
                    self._table,
                    self._select(), self._sub_select(), self._from(), self._where(cr), self._group_by()))

