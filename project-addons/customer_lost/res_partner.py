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

from openerp import models, fields, api


class res_partner(models.Model):

    _inherit = 'res.partner'

    customer_lost = fields.Boolean('Customer lost', readonly=True)

    def run_scheduler_custmer_lost(self, cr, uid, automatic=False,
                                   use_new_cursor=False, context=None):
        """
            Mark customers who did not buy in a period of time like lost
        """
        purchase_obj = self.pool.get('purchase.order')
        last_purchase_date = '2014-01-14'
        partner_ids = self.search(cr, uid, [], context=context)
        customer_lost = []
        customer_not_lost = []
        for partner in self.browse(cr, uid, partner_ids, context):
            purchase_ids = purchase_obj.search(cr, uid,
                                               [('partner_id', '=', partner.id),
                                                ('date_order', '>=', last_purchase_date)],
                                               context=context)
            if not purchase_ids:
                purchase_ids = purchase_obj.search(cr, uid, [('partner_id', '=', partner.id)], context=context)
                if purchase_ids:
                    customer_lost.append(partner.id)
            else:
                customer_no_lost.append(partner.id)
        self.write(cr, uid, customer_lost, {'customer_lost': True}, context)
        self.write(cr, uid, customer_no_lost, {'customer_lost': False}, context)
        return

