# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
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

from openerp.osv import fields, orm
from tools.translate import _

import StringIO
from report.interface import report_int
from datetime import datetime
import time
from pychart import *
import pychart.legend


class res.partner(orm.Model):

    _inherit = 'res.partner'

    _columns = {
        'sale_graphic': fields.binary("Sale graphic"),
    }

    def run_scheduler_grpahic(self, cr, uid, automatic=False,
                              use_new_cursor=False, context=None):
        """
            Generate the graphs of sales and link it to the partner
        """
        partner_obj = self.pool.get('res.partner')
        if context is None:
            context = {}

        partner_ids = partner_obj.search(cr, uid, [('customer', '=', True)], context=context)
        for partner in partner_obj.browse(cr, uid, partner_ids, context):
            pass
        return

