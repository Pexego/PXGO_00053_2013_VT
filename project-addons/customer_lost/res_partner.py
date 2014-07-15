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

from openerp import models, fields
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class res_partner(models.Model):

    _inherit = 'res.partner'

    customer_lost = fields.Boolean('Customer lost', readonly=True)
    last_sale_date = fields.Date('Last sale')
    customer_win = fields.Boolean('Customer win', readonly=True)

    _defaults = {
        'customer_win': False,
        'customer_lost': False,
    }

    def run_scheduler_custmer_lost(self, cr, uid, automatic=False,
                                   use_new_cursor=False, context=None):
        sale_obj = self.pool.get('sale.order')
        min_sale_date = (date.today() + relativedelta(months=-6))
        max_sale_date = (date.today() + relativedelta(years=-1))
        partner_ids = self.search(cr, uid, [], context=context)
        for partner in self.browse(cr, uid, partner_ids, context):
            last_sale_id = sale_obj.search(cr, uid,
                                           [('partner_id', '=', partner.id),
                                            ('state', 'in', ['progress',
                                                             'manual',
                                                             'shipping_except',
                                                             'invoice_except',
                                                             'done'])],
                                           limit=1, order='date_order',
                                           context=context)
            if last_sale_id:
                last_sale_str = sale_obj.browse(cr, uid, last_sale_id[0],
                                                context).date_order
                last_sale_date = datetime.strptime(last_sale_str[:10],
                                                   "%Y-%m-%d").date()

                # No puede ser perdido
                if last_sale_date >= min_sale_date:
                    # si estaba como perdido se marca como ganado
                    if partner.customer_lost:
                        self.write(cr, uid, [partner.id],
                                   {'customer_lost': False,
                                    'customer_win': True}, context)
                else:
                    # se comprueba si tiene compras anteriores para
                    # considerarlo como perdido
                    if last_sale_date >= max_sale_date:
                        self.write(cr, uid, [partner.id],
                                   {'customer_lost': True,
                                    'customer_win': False}, context)

        return
