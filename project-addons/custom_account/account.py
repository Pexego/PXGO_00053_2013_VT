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

    def default_attach_picking(self):
        r=self.env['stock.picking'].browse(self.env.context.get('active_ids', False))[0].partner_id.attach_picking
        return r

    attach_picking = fields.Boolean('Attach picking' , default= default_attach_picking)
    picking_ids = fields.One2many('stock.picking', string='pickings',
                                  compute='_get_picking_ids')
    country_id = fields.Many2one('res.country', 'Country',
                                 related="partner_id.country_id",
                                 readonly=True, store=True)

    @api.multi
    @api.depends('invoice_line')
    def _get_picking_ids(self):
        for invoice in self:
            invoice.picking_ids = invoice.\
                mapped('invoice_line.move_id.picking_id').sorted()
