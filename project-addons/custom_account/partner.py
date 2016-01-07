# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Kiko Sanchez <kiko@comunitea.com>$
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
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import fields, models, api


class Partner(models.Model):

    _inherit = "res.partner"

    @api.one
    def _pending_orders_amount(self):
        sales = self.env['sale.order'].\
            search([('partner_id', 'child_of', [self.id]),
                    ('state', 'not in', ['draft', 'cancel', 'wait_risk',
                                         'history'])])
        total = 0.0
        for order in sales:
            total += order.amount_total - order.amount_invoiced

        self.pending_orders_amount = total

    attach_picking = fields.Boolean("Attach picking")
    pending_orders_amount = fields.Float(compute="_pending_orders_amount",
                                         string='Uninvoiced Orders')
