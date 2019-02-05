# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
from openerp import models, fields, api, tools, _
import copy


class AccountFollowupPrint(models.Model):
    _inherit = 'account_followup.print'

    """
    Funcion para automatizar el envio de correos cada dia.
    Es la misma funcion que do_process de account_followup.print
    pero modificando la fecha por la fecha de hoy
    """

    @api.model
    def automatice_process(self):
        wzd = self.create({'date': fields.Date.today()})
        wzd.do_process()

    @api.multi
    def _get_partners_followp(self):
        res = super(AccountFollowupPrint, self)._get_partners_followp()
        iter_res = copy.deepcopy(res)
        company_id = self.company_id.id

        # Avoid sending followup account emails to suppliers
        self.env.cr.execute(
            "SELECT l.id "
            "FROM account_move_line AS l "
            "INNER JOIN account_move am on am.id = l.move_id "
            "LEFT JOIN account_account AS a "
            "ON (l.account_id=a.id) "
            "LEFT JOIN res_partner AS rp ON (l.partner_id = rp.id) "
            "WHERE (l.full_reconcile_id IS NULL) "
            "AND (a.internal_type='receivable') "
            "AND (am.state<>'draft') "
            "AND (l.partner_id is NOT NULL) "
            "AND (l.debit > 0) "
            "AND (l.company_id = %s) "
            "AND (l.blocked = False) "
            "AND (rp.customer = False) "
            "AND (rp.supplier = True) "
            "ORDER BY l.date", (company_id,))

        move_lines = self.env.cr.fetchall()
        move_line_supplier = [str(id) for id in move_lines]

        for lines in iter_res['to_update']:
            if lines in move_line_supplier:
                supplier_id = res['to_update'][lines]['partner_id']
                res['to_update'].pop(lines)
                res['partner_ids'].remove(supplier_id)
        return res

