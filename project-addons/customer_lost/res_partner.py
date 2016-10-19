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
    last_sale_date = fields.Date('Last sale', readonly=True)
    customer_win = fields.Boolean('Customer win', readonly=True)

    _defaults = {
        'customer_win': False,
        'customer_lost': False,
    }

    def _get_month_parameters(self, cr, uid, context):
        """
            Devuelve los meses configurados en los parametros en una tupla.
        """
        param_pool = self.pool.get("ir.config_parameter")
        config_min_months_id = param_pool.search(cr, uid,
                                                 [('key', '=',
                                                   'min.months.last.purchase')],
                                                 context=context)
        config_max_months_id = param_pool.search(cr, uid,
                                                 [('key', '=',
                                                   'max.months.last.purchase')],
                                                 context=context)
        if not config_min_months_id or not config_max_months_id:
            return (False, False)
        config_min_months = param_pool.browse(cr, uid, config_min_months_id,
                                              context)[0]
        config_max_months = param_pool.browse(cr, uid, config_max_months_id,
                                              context)[0]

        months_min_sale = int(config_min_months.value)
        months_max_sale = int(config_max_months.value)
        return (months_min_sale, months_max_sale)

    def run_scheduler_custmer_lost(self, cr, uid, automatic=False,
                                   use_new_cursor=False, context=None):
        sale_obj = self.pool.get('sale.order')

        months_min_sale, months_max_sale = self._get_month_parameters(cr, uid,
                                                                      context)
        if not months_min_sale or not months_max_sale:
            return
        min_sale_date = date.today() + relativedelta(months=-months_min_sale)
        max_sale_date = date.today() + relativedelta(months=-months_max_sale)
        partner_ids = self.search(cr, uid, [('customer', '=', True),
                                            ('is_company', '=', True)],
                                  context=context)
        for partner in self.browse(cr, uid, partner_ids, context):
            last_sale_id = sale_obj.search(cr, uid,
                                           [('partner_id', '=', partner.id),
                                            ('state', 'in', ['progress',
                                                             'manual',
                                                             'shipping_except',
                                                             'invoice_except',
                                                             'done'])],
                                           limit=1, order='date_order desc',
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
                                    'customer_win': True,
                                    'last_sale_date': last_sale_date}, context)
                        continue
                else:
                    # se comprueba si tiene compras anteriores para
                    # considerarlo como perdido
                    if last_sale_date >= max_sale_date:
                        self.write(cr, uid, [partner.id],
                                   {'customer_lost': True,
                                    'customer_win': False,
                                    'last_sale_date': last_sale_date}, context)
                        continue
                self.write(cr, uid, [partner.id], {'last_sale_date': last_sale_date}, context)
        return
