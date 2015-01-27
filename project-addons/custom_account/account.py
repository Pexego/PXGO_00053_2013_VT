# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    move_id = fields.Many2one('stock.move', 'Move')


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    attach_picking = fields.Boolean('Attach picking')
    picking_ids = fields.One2many('stock.picking', string='pickings',
                                  compute='_get_picking_ids')

    @api.multi
    @api.depends('invoice_line')
    def _get_picking_ids(self):
        for invoice in self:
            invoice.picking_ids = invoice.mapped('invoice_line.move_id.picking_id').sorted()
