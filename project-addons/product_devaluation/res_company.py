# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sánchez <kiko@comunitea.com>$
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

from openerp import fields, models, api
from openerp.exceptions import ValidationError


class res_company(models.Model):
    _inherit = "res.company"

    devaluation_journal_id = fields.Many2one('account.journal', 'Journal')
    devaluation_account_provision_id = fields.Many2one('account.account', 'Provision Account',
                                                       domain=[('type', '<>', 'view'), ('type', '<>', 'closed')])
    devaluation_account_debit_id = fields.Many2one('account.account', 'Debit Account',
                                                   domain=[('type', '<>', 'view'), ('type', '<>', 'closed')])
    devaluation_account_credit_id = fields.Many2one('account.account', 'Credit Account',
                                                    domain=[('type', '<>', 'view'), ('type', '<>', 'closed')])
