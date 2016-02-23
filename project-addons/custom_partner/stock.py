# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp import models, fields, api, exceptions, _


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    invoice_type_id = fields.Many2one('res.partner.invoice.type', 'Invoice type')

    @api.model
    def create(self, args):
        res = super(StockPicking, self).create(args)
        if res.picking_type_code == 'outgoing' and res.partner_id:
            res.invoice_type_id = res.partner_id.commercial_partner_id.\
                invoice_type_id.id
        return res

    def onchange_partner_in(self, cr, uid, ids, partner_id=None, context=None):
        res = super(StockPicking, self).onchange_partner_in(cr, uid, ids,
                                                            partner_id,
                                                            context)
        if partner_id:
            part = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if part.invoice_type_id or \
                    part.commercial_partner_id.invoice_type_id:
                value = part.invoice_type_id.id or \
                    part.commercial_partner_id.invoice_type_id.id
                if res.get('value', False):
                    res['value']['invoice_type_id'] = value
                else:
                    res['value'] = {'invoice_type_id': value}
        return res

