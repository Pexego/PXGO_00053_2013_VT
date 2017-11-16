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
from openerp import models, fields, api, _


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
