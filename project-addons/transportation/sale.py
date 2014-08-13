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


class sale_order(models.Model):

    _inherit = 'sale.order'
    # TODO: Establecer domain para que solo aparezcan los servicios
    #       que tiene el transportista seleccionado.
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
