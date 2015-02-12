# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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

from openerp import fields, models, api, _, exceptions


class StockPicking(models.Model):

    _inherit = "stock.picking"

    with_incidences = fields.Boolean('With incidences')#, readonly=True)

    @api.one
    def action_ignore_incidences(self):
        self.with_incidences = False
        self.message_post(body=_("User %s ignored the last incidence.") %
                          (self.env.user.name))

    @api.multi
    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        for pick in self:
            pick.write({'with_incidences': False})
        return res

    @api.multi
    def unassign_picking(self):
        self.do_unreserve()

    @api.cr_uid_ids_context
    def do_enter_transfer_details(self, cr, uid, picking, context=None):
        for pick in self.pool['stock.picking'].browse(cr, uid, picking,
                                                      context=context):
            if pick.with_incidences:
                raise exceptions.Warning(_("Cannot process picking with "
                                           "incidences. Please fix or "
                                           "ignore it."))
        return super(StockPicking, self).do_enter_transfer_details(cr, uid,
                                                                   picking,
                                                                   context)

    @api.multi
    def action_done(self):
        for pick in self:
            if pick.with_incidences:
                raise exceptions.Warning(_("Cannot process picking with "
                                           "incidences. Please fix or "
                                           "ignore it."))
        return super(StockPicking, self).action_done()
