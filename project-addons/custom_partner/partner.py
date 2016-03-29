# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pcomunitea.com>$
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


class ResPartnerInvoiceType(models.Model):

    _name = 'res.partner.invoice.type'

    name = fields.Char('Name', required=True)


class ResPartner(models.Model):

    _inherit = "res.partner"

    @api.one
    def _get_products_sold(self):
        lines = self.env["sale.order.line"].read_group([('order_partner_id',
                                                         '=', self.id)],
                                                       ['product_id'],
                                                       groupby="product_id")
        self.sale_product_count = len(lines)

    web = fields.Boolean("Web", help="Created from web", copy=False)
    sale_product_count = fields.Integer(compute=_get_products_sold,
                                        string="# Products sold",
                                        readonly=True)
    invoice_type_id = fields.Many2one('res.partner.invoice.type',
                                      'Invoice type')
    dropship = fields.Boolean("Dropship")

    @api.model
    def create(self, vals):
        if vals.get('dropship', False):
            vals['active'] = False
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('dropship', False):
            vals['active'] = False
        return super(ResPartner, self).write(vals)
