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

from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):

    _inherit = 'res.partner'

    customer_lost = fields.Boolean('Customer lost', readonly=True, default=False)
    last_sale_date = fields.Date('Last sale', readonly=True)
    customer_win = fields.Boolean('Customer win', readonly=True, default=False)

    @api.multi
    def _get_month_parameters(self):
        """
            Devuelve los meses configurados en los parametros en una tupla.
        """
        months_min_sale = self.env['ir.config_parameter'].get_param('min.months.last.purchase')
        months_max_sale = self.env['ir.config_parameter'].get_param('max.months.last.purchase')
        if not months_min_sale or not months_max_sale:
            return False, False
        else:
            return int(months_min_sale), int(months_max_sale)

    @api.model
    def run_scheduler_custmer_lost(self,automatic=False, use_new_cursor=False):
        sale_obj = self.env['sale.order']
        months_min_sale, months_max_sale = self._get_month_parameters()
        if not months_min_sale or not months_max_sale:
            return
        min_sale_date = date.today() + relativedelta(months=-months_min_sale)
        max_sale_date = date.today() + relativedelta(months=-months_max_sale)
        partner_ids = self.search([('customer', '=', True), ('is_company', '=', True)])
        for partner in partner_ids:
            last_sale_id = sale_obj.search([('partner_id', '=', partner.id),
                                            ('state', 'in', ['progress',
                                                             'manual',
                                                             'shipping_except',
                                                             'invoice_except',
                                                             'sale',
                                                             'done'])],
                                           limit=1, order='date_order desc')
            if last_sale_id:
                last_sale_str = last_sale_id.date_order
                last_sale_date = datetime.strptime(last_sale_str[:10], "%Y-%m-%d").date()

                # No puede ser perdido
                if last_sale_date >= min_sale_date:
                    # si estaba como perdido se marca como ganado
                    if partner.customer_lost:
                        partner.write({'customer_lost': False,
                                       'customer_win': True,
                                       'last_sale_date': last_sale_date})
                        continue
                else:
                    # se comprueba si tiene compras anteriores para
                    # considerarlo como perdido
                    if last_sale_date >= max_sale_date:
                        partner.write({'customer_lost': True,
                                       'customer_win': False,
                                       'last_sale_date': last_sale_date})
                        continue
                partner.write({'last_sale_date': last_sale_date})
        return
