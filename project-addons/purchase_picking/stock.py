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


class stock_move(models.Model):

    _inherit = 'stock.move'

    partner_id = fields.Many2one('res.partner', 'Partner')


    def _get_master_data(self, cr, uid, move, company, context=None):
        ''' returns a tuple (browse_record(res.partner), ID(res.users),
            ID(res.currency)'''
        return move.partner_id, uid, company.currency_id.id

    @api.one
    def write(self, vals):
        if self.picking_type_id.code == 'incoming':
            if 'date_expected' in vals.keys():
                reservations = self.env['stock.reservation'].search(
                    [('product_id', '=', self.product_id.id),
                     ('state', '=', 'confirmed')])
                # no se necesita hacer browse.
                # reservations = self.env['stock.reservation'].browse(reservation_ids)
                for reservation in reservations:
                    reservation.date_planned = self.date_expected
                    if not reservation.sale_id:
                        continue
                    sale = reservation.sale_id
                    followers = sale.message_follower_ids
                    sale.message_post(body="The date planned was changed.",
                                      subtype='mt_comment',
                                      partner_ids=followers)
        return super(stock_move, self).write(vals)
