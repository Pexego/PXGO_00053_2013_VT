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

from openerp import models


class MrpRepairLine(models.Model):

    _inherit = "mrp.repair.line"

    def onchange_operation_type(self, cr, uid, ids, type, guarantee_limit,
                                company_id=False, context=None):
        res = super(MrpRepairLine, self).\
            onchange_operation_type(cr, uid, ids, type, guarantee_limit,
                                    company_id=company_id, context=context)
        if type != "add" and context.get("cur_location_id", False):
            res['value']['location_id'] = context['cur_location_id']

        return res
