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
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class Partner(models.Model):

    _inherit = 'res.partner'

    amount_shipping_balance = fields.Float("Shipping Balance", help="Shipping Balance Amount", compute='_get_shipping_balance')
    shipping_balance_ids = fields.One2many("shipping.balance", "partner_id", string="Listado Saldos de Envíos")

    @api.multi
    @api.depends('shipping_balance_ids', 'shipping_balance_ids.amount')
    def _get_shipping_balance(self):
        for partner in self:
            final_amount = 0.00
            for d in partner.shipping_balance_ids:
                final_amount += (d.amount or 0.00) * (d.aproved_ok or 0.00)

            if final_amount >= 0:
                partner.amount_shipping_balance = final_amount
            else:
                raise ValidationError("Shipping Balance amount must be > 0")
