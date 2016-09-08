# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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

from openerp import fields, models, api, registry
from datetime import datetime, timedelta


class StockMove(models.Model):

    _inherit = "stock.move"

    reservation_ids = fields.One2many("stock.reservation", "move_id",
                                      "Reservations", readonly=True)


class stock_reservation(models.Model):

    _inherit = 'stock.reservation'

    unique_js_id = fields.Char('', size=64)

    @api.model
    def delete_orphan_reserves(self):
        now = fields.Datetime.now()
        d = datetime.strptime(now, '%Y-%m-%d %H:%M:%S') + \
            timedelta(minutes=-30)
        last_date = datetime.strftime(d, '%Y-%m-%d %H:%M:%S')
        reserves = self.search([('create_date', '<=', last_date),
                                ('sale_line_id', '=', False),
                                ('mrp_id', '=', False),
                                ('claim_id', '=', False),
                                ('move_id.state', 'not in', ['done',
                                                             'cancel'])])

        if reserves:
            reserves.unlink()

        reserves_loc = self.env.ref("stock_reserve.stock_location_reservation")
        moves = self.env["stock.move"].search([('location_dest_id', '=',
                                                reserves_loc.id),
                                               ('state', '!=', "cancel"),
                                               ('reservation_ids', '=',
                                                False)])
        if moves:
            moves.action_cancel()

        return True

    @api.model
    def create(self, vals):
        res = super(stock_reservation, self).create(vals)
        if vals.get('unique_js_id', False) and \
                not vals.get('sale_line_id', False):
            with registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid,
                                          self.env.context)

                new_env.cr.execute("select id from sale_order_line where "
                                   "unique_js_id = '%s'" % vals['unique_js_id'])

                lines = new_env.cr.fetchone()
                if lines:
                    self.with_env(new_env).write({'sale_line_id': lines[0]})
                new_env.cr.commit()

        return res
