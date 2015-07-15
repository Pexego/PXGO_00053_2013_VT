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

class Shipping_Balance(models.Model):

    _name = 'shipping.balance'

    partner_id = fields.Many2one('res.partner', 'Partner')
    repair_id = fields.Many2one('mrp.repair', required=False)
    sale_id = fields.Many2one('sale.order', required=False)
    amount = fields.Float ('Amount', default=0)
    aproved_ok = fields.Boolean("Aproved", default=True, help="Must be aproved before use")
    balance = fields.Boolean ("Balance", help="True > positive")
    final_id=fields.Char("Refers to", compute ="get_refer_to")

    @api.one
    def get_refer_to(self):
        if self.balance == False:
            self.final_id=self.sale_id.name
        else:
            self.final_id=self.repair_id.name
        return True

