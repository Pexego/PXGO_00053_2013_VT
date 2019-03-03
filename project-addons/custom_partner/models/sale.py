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
from odoo import models, fields, api, exceptions, _


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    invoice_type_id = fields.Many2one('res.partner.invoice.type', "Invoice type")

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        for order in self:
            if order.partner_id:
                part = order.partner_id
                self.invoice_type_id = part.invoice_type_id and part.invoice_type_id.id \
                    or part.commercial_partner_id.invoice_type_id and part.commercial_partner_id.invoice_type_id.id \
                    or False
