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
from datetime import date


class sale_order(models.Model):

    _inherit = 'sale.order'
    transporter_id = fields.Many2one('transportation.transporter',
                                     'transporter')
    service_id = fields.Many2one('transportation.service',
                                 'Transport service')

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part,
                                                          context)
        if part:
            values = res.get('value', {})
            partner = self.pool.get('res.partner').browse(cr, uid, part,
                                                          context)
            values['transporter_id'] = partner.transporter_id.id
            values['service_id'] = partner.service_id.id
            res['value'] = values
        return res

    @api.onchange('transporter_id')
    def onchange_transporter_id(self):
        service_ids = [x.id for x in self.transporter_id.service_ids]
        if service_ids:
            if self.service_id.id not in service_ids:
                self.service_id = False

            return {'domain': {'service_id': [('id', 'in', service_ids)]}}
        all_services  = [x.id for x in self.env['transportation.service'].search([])]
        return {'domain': {'service_id': [('id', 'in', all_services)]}}

    @api.multi
    def action_wait(self):
        super(sale_order, self).action_wait()
        daily_obj = self.env['transportation.daily']
        trans_daily = daily_obj.search([('date', '=', date.today()), ('area_id', '=', self.partner_id.area_id.id)])
        if trans_daily:
            trans_daily = trans_daily[0]
        else:
            trans_daily = daily_obj.create({'date': date.today(), 'area_id': self.partner_id.area_id.id})

        if self.transporter_id:
            trans_daily.assign_transporter(self.transporter_id)
        else:
            transporter = trans_daily.get_transporter(self.partner_id)
            if transporter:
                self.transporter_id = transporter
                trans_daily.assign_transporter(transporter)
        return True

