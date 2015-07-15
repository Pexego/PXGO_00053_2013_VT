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

from openerp.exceptions import ValidationError

class Partner(models.Model):

    _inherit = "res.partner"

    amount_shipping_balance = fields.Float("Shipping Balance", help = "Shipping Balance Amount", compute='_get_shipping_balance')
    shipping_balance_ids = fields.One2many ("shipping.balance","partner_id", string="Listado Saldos de Envíos")

    @api.one
    @api.depends('shipping_balance_ids', 'shipping_balance_ids.amount')
    def _get_shipping_balance(self):
        final_amount=0.00
        for d in self.shipping_balance_ids:
            final_amount += (d.amount or 0.00)*(d.aproved_ok or 0.00)

        if final_amount >= 0:
            self.amount_shipping_balance = final_amount
        else:
            raise ValidationError("Shipping Balance amount must be > 0")

        return True

    @api.constrains('amount_shipping_balance')
    def _check_amount_shipping_balance(self):

        if self.amount_shipping_balance < 0:
            raise ValidationError("Shipping Balance amount must be > 0")
